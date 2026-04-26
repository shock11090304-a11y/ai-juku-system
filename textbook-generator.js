// ==========================================================================
// Textbook Generator — PDF教材向けの構造化コンテンツ生成
// ==========================================================================

// 科目別の単元マスター（複数選択可能）
const TB_UNITS_BY_SUBJECT = {
  '英語（英検準1級）': ['単語強化 (Part1)', 'リーディング (Part2 長文)', 'リスニング Part1 (会話)', 'リスニング Part2 (文章)', 'ライティング 要約 (60-70語・2024年度新設)', 'ライティング 意見論述 (120-150語)', '二次面接対策', '過去問演習'],
  '英語（英検2級）': ['単語 (2600語)', 'リーディング', 'ライティング 意見論述 (80-100語)', 'リスニング', '面接 (質問応答)', '過去問演習'],
  '英語（共通テスト）': ['リーディング (6題)', 'リスニング (6題)', '速読トレーニング', '時間配分', '選択肢の絞り方', '頻出文法問題'],
  '英語（東大2次）': ['要約問題', '段落整序', '和文英訳', '自由英作文', '長文読解', 'リスニング', '東大独自文法'],
  '英語（高校英文法）': ['関係代名詞', '関係副詞', '仮定法', '時制（完了形）', '時制（進行形）', '助動詞', '不定詞', '動名詞', '分詞', '分詞構文', '比較', '接続詞', '前置詞', '冠詞', '受動態', '話法', '倒置', '強調', '省略'],
  '英語（中学英文法）': ['be動詞', '一般動詞', '疑問詞', '進行形', '未来形', '過去形', '助動詞 (can/will/must)', '比較', '受動態', '現在完了', '不定詞・動名詞', '分詞', '関係代名詞 (基礎)', '接続詞'],
  '数学ⅠA': ['数と式', '1次関数', '2次関数', '2次方程式・2次不等式', '三角比', '集合と論理', 'データの分析', '場合の数', '確率', '整数の性質', '図形の性質'],
  '数学ⅡB': ['式と証明', '複素数と方程式', '図形と方程式', '三角関数', '指数関数・対数関数', '微分法', '積分法', '数列', 'ベクトル (平面)', 'ベクトル (空間)'],
  '数学Ⅲ': ['極限', '関数と極限', '微分法 (数III)', '微分の応用', '積分法 (数III)', '積分の応用', '面積・体積', '媒介変数表示', '曲線の長さ', '回転体の体積'],
  '数学C': ['ベクトル (平面)', 'ベクトル (空間)', '複素数平面', '複素数平面と回転', '式と曲線 (2次曲線)', '極座標と極方程式', '数学的な表現の工夫', '※2025年度新課程で数ⅡB・数Ⅲから独立'],
  '国語（現代文）': ['評論文読解', '小説読解', '随筆読解', 'キーワード・語彙', '記述問題 (40字)', '記述問題 (100字)', '抜き出し問題', '空所補充', '要旨把握', '指示語問題', '慣用句・四字熟語'],
  '国語（古文）': ['動詞の活用', '形容詞・形容動詞の活用', '助動詞 (る・らる)', '助動詞 (す・さす・しむ)', '助動詞 (き・けり・つ・ぬ)', '助動詞 (む・むず・じ・まし)', '助動詞 (べし)', '助詞', '敬語 (尊敬)', '敬語 (謙譲)', '敬語 (丁寧)', '二重敬語', '和歌修辞法', '掛詞・縁語', '古文常識', '源氏物語', '枕草子', '徒然草', '伊勢物語', '古今和歌集'],
  '国語（漢文）': ['訓読の基本', '返り点', '再読文字', '使役形', '受身形', '否定形', '疑問形', '反語形', '比較形', '限定形', '仮定形', '抑揚形', '白文読解', '漢詩'],
  '物理基礎・物理': ['等加速度運動', '落体の運動', '力のつりあい', '運動方程式', '摩擦力', '仕事とエネルギー', '力積と運動量', '円運動', '単振動', '万有引力', '波動の基本', '波の干渉', '音波・ドップラー効果', '光 (反射・屈折)', '熱力学', '電場と電位', 'コンデンサー', '直流回路', '電流と磁場', '電磁誘導', '交流', '原子物理'],
  '化学基礎・化学': ['物質量 (モル計算)', '化学反応式', '酸と塩基', '酸化還元反応', '電池・電気分解', '熱化学', '反応速度', '化学平衡', '気体の法則', '溶液の性質', '無機 (非金属元素)', '無機 (典型金属)', '無機 (遷移元素)', '有機 (脂肪族)', '有機 (芳香族)', '糖類', 'アミノ酸・タンパク質', '高分子化合物'],
  '生物基礎・生物': ['細胞の構造', '代謝 (呼吸・発酵)', '代謝 (光合成)', 'DNA と遺伝情報', '遺伝子の発現', 'メンデル遺伝', '連鎖と組換え', '発生 (動物)', '発生 (植物)', '体液・循環系', '腎臓・肝臓', '神経系', '内分泌系', '免疫', '生態系', '進化・系統'],
  '日本史': ['旧石器・縄文', '弥生時代', '古墳時代', '飛鳥時代', '奈良時代', '平安時代', '鎌倉時代', '室町時代', '戦国時代', '安土桃山時代', '江戸時代 (初期)', '江戸時代 (中期)', '江戸時代 (後期)', '幕末', '明治時代', '大正時代', '昭和戦前', '戦後史', '文化史 (古代)', '文化史 (中世)', '文化史 (近世)', '文化史 (近代)'],
  '世界史': ['古代オリエント', 'ギリシア・ローマ', '中国古代 (殷・周・秦・漢)', '中国中世 (隋・唐)', '中国近世 (宋・元・明・清)', 'イスラム世界', 'ヨーロッパ中世', 'ルネサンス・宗教改革', '大航海時代', '絶対主義', '市民革命', 'アメリカ独立', 'フランス革命', 'ウィーン体制', '産業革命', '帝国主義', '第一次世界大戦', '第二次世界大戦', '冷戦', '戦後史・現代', 'インド史', '東南アジア史', 'アフリカ史', 'ラテンアメリカ史'],

  // ==========================================================================
  // 大学別カリキュラム（MARCH以上／難関国公立）
  // ==========================================================================
  '英語（英検1級）': ['単語 (10000〜15000語)', '長文読解 (1000語級)', 'ライティング 要約 (90-110語・2024年度新設)', 'ライティング 意見論述 (200-240語)', 'リスニング (講義・議論)', '語法・文法 (高度)', '二次面接 (2分スピーチ)', '過去問演習'],
  '英語（MARCH）': ['長文読解 (600〜800語)', '文法・語法 (Vintage / Next Stage レベル)', '整序英作文', '空所補充', '同義語問題', '会話文読解', '文章要約 (40〜60字)', '過去問研究 (明治・青学・立教・中央・法政)'],
  '英語（関関同立）': ['長文読解 (700〜1000語)', '文法・語法 (標準)', '整序英作文', '和訳問題', '内容一致', '英語面接対策（立命館・同志社国際）', '過去問研究 (関・関学・同志社・立命館)'],
  '英語（早慶上智）': ['超長文読解 (1500〜2000語)', '語法・文法 (ランダム高難度)', '自由英作文 (80〜150語)', '和文英訳 (記述)', 'テーマ論述', '会話表現・イディオム', '要約問題 (政経)', '過去問研究 (早大政経/商/文/法/理工、慶大経済/商/法/文/SFC、上智)'],
  '英語（難関国公立2次）': ['長文和訳 (下線部3-4箇所)', '英文和訳 (パラグラフ要約)', '自由英作文 (80〜150語)', '和文英訳 (1〜3文)', '内容説明 (記述)', '英文和訳の論理的展開', 'リスニング (講義型)', '過去問研究 (阪大・名大・東北・九大・北大・神戸・筑波)'],
  '英語（京大2次）': ['英文和訳 (下線部 超長文)', '和文英訳 (150〜200語 長文和訳)', '内容解釈の記述', '抽象的な英文の解釈', '比喩・レトリックの訳出', '論理展開の把握', '過去問研究 (京大直近20年)'],
  '英語（医学部）': ['医系長文 (医療・倫理)', '医学語彙', '自由英作文 (医療トピック)', '会話問題 (面接練習)', '和文英訳 (症例記述)', '要約問題', '過去問研究 (旧帝医・慶應医・順天堂・慈恵)'],

  '数学（共通テスト）': ['数ⅠA 大問1 (数と式・2次関数)', '数ⅠA 大問2 (図形と計量・データの分析)', '数ⅠA 大問3 (場合の数と確率)', '数ⅠA 大問4 (整数)', '数ⅠA 大問5 (図形の性質)', '数ⅡB 大問1 (三角・指数対数)', '数ⅡB 大問2 (微積分)', '数ⅡB 大問3 (数列)', '数ⅡB 大問4 (ベクトル)', '時間配分戦略', 'マーク式解法テクニック'],
  '数学（MARCH・関関同立）': ['青チャート例題レベル', '典型パターン網羅', '場合の数・確率 (MARCH頻出)', '数列 (漸化式)', 'ベクトル (空間)', '微積分 (標準)', '対数・三角関数', '整数問題 (標準)', '過去問研究 (明治・青学・立教・中央・法政・関関同立)'],
  '数学（早慶上智）': ['1対1対応の演習レベル', '確率漸化式', '整数論 (mod計算)', '複素数平面 (応用)', '微積分の応用', '空間ベクトル', '軌跡と領域', '論証問題', '過去問研究 (早大理工・商・社学、慶大経済・商・理工、上智)'],
  '数学（難関国公立理系）': ['微積分 (記述式論証)', '複素数平面 (軌跡・回転)', '空間ベクトル・空間図形', '確率 (漸化式・期待値)', '整数論 (合同式・素因数)', '数列の極限・級数', '微分方程式風の問題', '図形と方程式 (軌跡)', '過去問研究 (阪大・名大・東北・九大・北大・神戸・筑波・東工大)'],
  '数学（京大2次）': ['整数 (発想型)', '確率 (漸化式・独立性)', '微積分 (面積・体積・論証)', '極限 (はさみうち)', '軌跡と領域', '複素数平面 (軌跡)', '論証問題 (全ての整数nで示せ型)', '証明問題の論理展開', '過去問研究 (京大直近20年)'],
  '数学（東大2次）': ['整数 (合同式・素因数・証明)', '確率 (漸化式・場合の数)', '複素数平面 (軌跡・領域)', '微積分 (面積・体積・不等式)', '空間ベクトル・図形', '軌跡と領域 (媒介変数)', '極限と級数', '数列の漸化式', '図形の性質 (論証)', '過去問研究 (東大理系・文系 直近20年)'],
  '数学（医学部）': ['全範囲網羅 (数ⅠAⅡBⅢ)', '時間制約下の処理能力', '計算力強化', '典型問題の完全定着', '融合問題 (幾何+代数)', '確率 (条件付き・ベイズ)', '微積分 (速度・加速度)', '空間図形の計量', '過去問研究 (旧帝医・慶應医・順天堂・慈恵・防衛医)'],

  '国語（共通テスト）': ['現代文 大問1 (評論)', '現代文 大問2 (小説)', '実用文・複数テキスト読解', '古文 大問3 (物語・随筆)', '漢文 大問4 (史伝・論説)', '時間配分 (80分)', '選択肢の絞り方', '傍線部解釈のコツ'],
  '国語（MARCH・関関同立）': ['現代文 (評論・小説)', '古文 (助動詞・敬語)', '漢文 (句形)', '漢字・語彙問題', '空所補充', '内容一致', '要約記述', '過去問研究 (明治・立教・中央・法政・関関同立)'],
  '国語（早慶上智）': ['現代文 (高難度評論)', '古文 (高度文法・古典常識)', '漢文 (思想・史伝)', '記述問題 (100字〜200字)', '抜き出し問題', '論理展開の把握', '語彙・慣用句', '過去問研究 (早大文・商・社学・法、慶大文・法、上智文)'],
  '国語（難関国公立2次）': ['現代文 (長文評論・随筆)', '古文 (多様なジャンル読解)', '漢文 (論説・史伝)', '記述問題 (50〜100字)', '要旨把握', '論理展開の把握', '過去問研究 (阪大・名大・東北・九大・神戸・一橋)'],
  '国語（東大・京大）': ['東大現代文 (抽象度高い評論)', '東大現代文 (第4問 随筆)', '東大古文 (100字記述)', '東大漢文 (100字記述)', '京大現代文 (長文 記述)', '京大古文 (和歌含む)', '記述の論理性・キーワード網羅', '過去問研究 (東大・京大 直近20年)'],

  '物理（難関国公立・医学部）': ['力学 (単振動・円運動の融合)', '力学 (二体問題・衝突)', '電磁気 (コンデンサー過渡)', '電磁気 (電磁誘導・LC回路)', '熱力学 (断熱過程・P-V図)', '波動 (ドップラー・干渉)', '原子物理 (光電効果・コンプトン)', '記述論述の構造 (モデル化→方程式→吟味)', '過去問研究 (東大・京大・阪大・東工大・医学部)'],
  '化学（難関国公立・医学部）': ['理論化学 (熱化学・平衡)', '理論化学 (気体・溶液)', '理論化学 (反応速度論)', '無機化学 (金属イオン分離)', '無機化学 (典型元素)', '有機化学 (構造決定)', '有機化学 (反応機構)', '高分子 (糖・アミノ酸・合成)', '記述論証の精度', '過去問研究 (東大・京大・阪大・医学部)'],
  '生物（難関国公立・医学部）': ['遺伝 (連鎖・組換え・マッピング)', '分子生物学 (DNA複製・転写・翻訳)', '発生 (誘導・形態形成)', '神経生理 (活動電位・シナプス)', '免疫 (抗体産生・MHC)', '代謝 (電子伝達系・カルビン回路)', '実験考察問題', 'データ解析 (グラフ読取り)', '過去問研究 (東大・京大・阪大・医学部)'],

  '日本史（MARCH・関関同立）': ['古代〜中世の政治史', '近世 (江戸時代) 政治・経済', '幕末・明治維新', '近代 (大正〜昭和戦前)', '戦後史', '文化史 (MARCH頻出)', '史料読解問題', '過去問研究 (明治・青学・立教・中央・法政・関関同立)'],
  '日本史（早慶上智）': ['超細密な近現代史', '史料問題 (原文読解)', '文化史 (早慶頻出)', '外交史・経済史', '論述問題 (早大・慶大文)', '用語集レベル語彙', '過去問研究 (早大政経・商・文・社学、慶大文・経済・商)'],
  '日本史（東大論述）': ['論述 (120〜180字×大問4構成、合計600-800字)', '中小論述 (60〜90字の小問)', '複数史料の比較読解', '時期区分の論理性', '因果関係の明示', '指定語句の完全活用', '評価基準 (キーワード網羅・論理・史料引用)', '過去問研究 (東大日本史 直近30年)'],
  '日本史（一橋論述）': ['大論述 (400字×3問構成)', '近世経済史 (幕藩体制・商業)', '近現代経済史 (産業革命・戦後復興)', '史料読解＋論述', '論理展開の精度', '過去問研究 (一橋日本史 直近20年)'],
  '世界史（MARCH・関関同立）': ['ヨーロッパ近代史', '中国通史', 'イスラム史', '東南アジア・インド史', 'アメリカ史', '戦後史', '文化史', '過去問研究 (明治・青学・立教・中央・法政・関関同立)'],
  '世界史（早慶上智）': ['細密な地域史 (早大商=経済史、早大文=文化史)', '超広域論述', '用語集レベル語彙', '地域横断テーマ史 (産業革命・宗教改革・冷戦)', '史料問題', '過去問研究 (早大政経・商・文・社学・法、慶大文・経済、上智)'],
  '世界史（東大大論述）': ['大論述 (450〜600字、年度変動、指定語句8-10語付き)', '地域横断テーマ史の因果構造', '時系列でなく「原因→展開→結果」の論理展開', '地域間連関の明示', '指定語句の全てを本文中で使用', '冒頭1-2文で問いに直接解答', '評価観点 (キーワード網羅・論理・地域横断)', '過去問研究 (東大世界史 直近30年)'],

  // ==========================================================================
  // 地理系（2025年度新課程: 地理総合・地理探究）
  // ==========================================================================
  '地理総合・地理探究': ['系統地理 (地形・気候)', '系統地理 (人口・都市)', '系統地理 (農業・工業)', '系統地理 (資源・エネルギー)', '系統地理 (交通・通信・貿易)', '地誌 (アジア)', '地誌 (ヨーロッパ・ロシア)', '地誌 (アフリカ)', '地誌 (南北アメリカ)', '地誌 (オセアニア)', '地図と地理情報 (GIS)', '地域調査・フィールドワーク', '環境問題・SDGs'],
  '地理（共通テスト）': ['系統地理 頻出パターン', '地誌 頻出地域', '統計読取り (貿易統計・人口ピラミッド)', '地形図読解 (新旧対比)', '主題図・分布図', '時間配分・選択肢の絞り方'],
  '地理（東大論述）': ['系統地理の論述 (90-180字)', '地誌の複合論述', '統計表・主題図の読解+記述', '環境・都市・産業の時事論述', '過去問研究 (東大地理 直近20年)'],
  '地理（MARCH・関関同立）': ['系統地理の頻出テーマ', '地誌の頻出地域', '統計読取り基礎', '地形図読解', '過去問研究 (MARCH・関関同立 地理)'],

  // ==========================================================================
  // 公民系（2025年度新課程: 公共・倫理・政経）
  // ==========================================================================
  '公共・倫理': ['青年期の課題', '源流思想 (ギリシア・中国・インド)', '日本思想 (仏教・儒学・国学・近代思想家)', '西洋近代思想 (経験論・合理論・功利主義・カント)', '現代思想 (実存主義・構造主義・プラグマティズム)', '日本国憲法の基本原理', '基本的人権', '公共空間の形成'],
  '公共・政経': ['日本国憲法 (条文引用)', '国会・内閣・裁判所 (三権分立)', '選挙制度・地方自治', '市場経済の仕組み', '財政・金融', '国際経済 (為替・貿易・グローバル化)', '社会保障', '労働法制', '国際機関・条約'],
  '公民（共通テスト）': ['公共・倫理 頻出', '公共・政経 頻出', '時事問題対応', '図表・グラフ読取り', '時間配分'],
};

let tbSelectedUnits = [];

function renderTbUnits(subject) {
  const chipsContainer = document.getElementById('tbUnitChips');
  const hint = document.getElementById('tbUnitHint');
  const units = TB_UNITS_BY_SUBJECT[subject] || [];

  if (units.length === 0) {
    chipsContainer.innerHTML = `<p class="unit-hint">この科目の単元マスターは未登録。自由入力欄に記入してください。</p>`;
    return;
  }

  chipsContainer.innerHTML = units.map(u =>
    `<button type="button" class="unit-chip ${tbSelectedUnits.includes(u) ? 'selected' : ''}" data-unit="${escapeHtmlTb(u)}">${escapeHtmlTb(u)}</button>`
  ).join('');

  chipsContainer.querySelectorAll('.unit-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const unit = chip.dataset.unit;
      const idx = tbSelectedUnits.indexOf(unit);
      if (idx >= 0) {
        tbSelectedUnits.splice(idx, 1);
        chip.classList.remove('selected');
      } else {
        tbSelectedUnits.push(unit);
        chip.classList.add('selected');
      }
      updateTbSelectedBar();
    });
  });
}

function updateTbSelectedBar() {
  const bar = document.getElementById('tbUnitSelectedBar');
  const tags = document.getElementById('tbUnitSelectedTags');
  if (tbSelectedUnits.length === 0) {
    bar.style.display = 'none';
  } else {
    bar.style.display = 'flex';
    tags.textContent = tbSelectedUnits.join('、');
  }
  // Topic input にも同期
  const topicInput = document.getElementById('tbTopic');
  if (topicInput) {
    const existing = topicInput.value;
    const selectedText = tbSelectedUnits.join('、');
    // 既存のフリー入力を保持しつつ、選択された単元だけを先頭に表示
    topicInput.placeholder = tbSelectedUnits.length > 0
      ? `選択済: ${selectedText}（さらに自由追記もできます）`
      : '（上のチップを選択 / または自由記入も可）';
  }
}

function clearTbUnits() {
  tbSelectedUnits = [];
  document.querySelectorAll('.unit-chip').forEach(c => c.classList.remove('selected'));
  updateTbSelectedBar();
}

function escapeHtmlTb(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c]));
}

const API_URL = 'https://api.anthropic.com/v1/messages';
// クオリティ最優先 → Opus 4.7 を使用（料金は Sonnet の5倍だが市販テキスト品質の出力）
const MODEL_PREMIUM = 'claude-opus-4-7';
const MODEL_STANDARD = 'claude-sonnet-4-6';

let lastData = null;
let lastMd = '';
let lastHtml = '';
let lastPython = '';

function getApiKey() { return localStorage.getItem('ai_juku_api_key'); }

function updateMode() {
  // 生徒可視のため常に「🟢 AI接続中」固定
  const el = document.getElementById('modeIndicator');
  if (!el) return;
  el.textContent = '🟢 AI接続中';
  el.className = 'mode-badge live';
  el.title = getApiKey() ? 'AI機能 稼働中' : 'AI機能 稼働中 (準備中)';
}

async function generateTextbook() {
  const type = document.getElementById('tbType').value;
  const subject = document.getElementById('tbSubject').value;
  const freeTopic = document.getElementById('tbTopic').value.trim();
  const level = document.getElementById('tbLevel').value;
  const length = document.getElementById('tbLength').value;
  const elements = [...document.querySelectorAll('.checkbox-item input:checked')].map(c => c.value);
  const notes = document.getElementById('tbNotes').value.trim();

  // 選択された単元（チップ）と自由入力の合体
  const selectedUnits = tbSelectedUnits.join('、');
  const topic = [selectedUnits, freeTopic].filter(Boolean).join(' / ');

  if (!topic) { alert('単元をチップから選択するか、テーマを入力してください'); return; }

  const btn = document.getElementById('generateTbBtn');
  const result = document.getElementById('tbResult');
  const actions = document.getElementById('tbActions');
  const tabs = document.getElementById('viewTabs');

  btn.disabled = true;
  btn.textContent = '⏳ 生成中...';
  result.className = 'tb-result';
  result.innerHTML = '<div class="tb-placeholder"><div style="font-size:3rem;">⚙️</div><p>AIが教材を執筆中... (30-90秒)</p></div>';
  actions.style.display = 'none';
  tabs.style.display = 'none';

  const lengthMap = {
    short: '2000〜3000字',
    medium: '5000〜8000字',
    long: '10000〜15000字',
    exhaustive: '20000字以上',
  };

  const systemPrompt = `あなたは駿台・河合・Z会・東進で教鞭を執ってきた、その科目の第一線のプロ講師です。編集者として市販の受験参考書（『総合英語Forest』『青チャート』『現代文と格闘する』クラス）に匹敵する品質のテキスト教材を執筆します。

【品質基準 — すべて満たしてください】
✅ 単元の本質を初学者にも伝える比喩・具体例を最低2つ以上含める
✅ 例題は「なぜその解き方を選ぶか」という思考の発想から書く
✅ 失敗例・よくあるミスを具体的に示し、その原因と対策まで書く
✅ 別解がある場合は「どちらを選ぶべきか」の判断基準を明示
✅ 他単元・他科目との繋がりを明記（例: 関係代名詞の裏に英文構造理解がある）
✅ 類題の出題例（大学名・年度）を具体的に挙げる（記憶にある範囲で）
✅ 単なる暗記項目は「なぜそうなるのか」の原理まで掘り下げる
✅ 章末の「まとめ」は箇条書きの羅列でなく、体系として整理する

【絶対にやってはいけないこと】
❌ 「〇〇とは△△です」の定義だけで終わる
❌ 解答だけ書いて解説を省く
❌ 抽象的な表現（「重要です」「気をつけましょう」）で逃げる
❌ 中身のないTIPボックス（「頑張りましょう」等）

【分量目安】${lengthMap[length]}

【出力形式】厳密なJSONで、他のテキストや\`\`\`は一切含めず、以下の構造で返してください:
{
  "title": "教材タイトル",
  "subtitle": "サブタイトル",
  "subject": "${subject}",
  "topic": "${topic}",
  "level": "${level}",
  "sections": [
    {
      "type": "intro", "heading": "はじめに",
      "body": "本文..."
    },
    {
      "type": "theory", "heading": "基本事項",
      "body": "解説...",
      "table": [["列1","列2"], ["値","値"]]  // 比較表がある場合のみ
    },
    {
      "type": "tip", "title": "ポイント",
      "body": "コツ・覚え方..."
    },
    {
      "type": "warn", "title": "注意",
      "body": "よくあるミス..."
    },
    {
      "type": "example", "number": 1,
      "question": "問題文...",
      "thought": "解き方の発想・ステップバイステップの思考プロセス",
      "answer": "答え",
      "explanation": "詳しい解説..."
    },
    {
      "type": "practice", "number": 1,
      "question": "演習問題文"
    },
    {
      "type": "answer", "number": 1,
      "answer": "解答",
      "explanation": "解説"
    },
    {
      "type": "vocab",
      "items": [{"word":"単語","meaning":"意味","example":"例文"}]
    },
    {
      "type": "summary", "heading": "まとめ",
      "points": ["ポイント1", "ポイント2", "..."]
    }
  ]
}

含めるべき要素: ${elements.join(', ')}
${/数学/.test(subject) ? `
【数学教材の追加規律】
- 数式は全て LaTeX（インライン \\( ... \\)、ディスプレイ \\[ ... \\]）。全角記号や x^2 記法は禁止。JSON文字列内の \\ は \\\\ に、改行は \\n に必ずエスケープ。
- レベル「${level}」の履修範囲外の単元（例: 数ⅠA で微積分、中学生に三角関数）を勝手に持ち込まない。
- 例題・演習の解答は (方針)→(本解、場合分けを全列挙)→(結論、等号成立/範囲) の三段構成。
- 確率は独立性・試行の定義を明記、整数は mod の法を明示、図形・証明は「示すべきこと」を冒頭で宣言。
- 「よくあるミス」セクションに、独立性誤用・場合分け漏れ・等号成立忘れ・必要十分の取り違えなど、典型失点を最低2件は具体例で記す。
- 東大・京大・医学部過去問を例示する場合は「（出典: ◯◯大 20XX 理系 大問X、記憶に基づく再現）」と注記し、記憶が曖昧な場合は年度を詐称しない。
` : ''}${notes ? `\n追加要件:\n${notes}` : ''}`;

  // 過去問対応モード: 有効なら大問メタをプロンプトに注入
  const tbPastExamFragment = (() => {
    const toggle = document.getElementById('tbPastExamToggle');
    if (!toggle || !toggle.checked) return '';
    const univ = document.getElementById('tbPastExamUniv')?.value;
    const year = document.getElementById('tbPastExamYear')?.value;
    const subj = document.getElementById('tbPastExamSubject')?.value;
    const qFilter = document.getElementById('tbPastExamQuestion')?.value;
    if (!univ || !year || !subj || typeof buildPastExamPromptFragment !== 'function') return '';
    let 大問配列 = typeof getPastExamProblems === 'function' ? getPastExamProblems(univ, year, subj) : [];
    if (qFilter) 大問配列 = 大問配列.filter(p => String(p.大問) === qFilter);
    return '\n\n' + buildPastExamPromptFragment(univ, year, subj, 大問配列)
      + '\n\n**教材への反映**: 例題・演習・コラムに「${univ} ${year}年度 大問X 類題」という見出しで該当形式の問題を配置し、解説内で「${univ}での典型失点」「この大学特有の採点基準」に言及してください。'.replace(/\$\{univ\}/g, univ).replace(/\$\{year\}/g, year);
  })();

  const userMsg = `教材タイプ: ${getTypeLabel(type)}
科目: ${subject}
単元: ${topic}
レベル: ${level}
分量: ${lengthMap[length]}
含める要素: ${elements.join(', ')}${tbPastExamFragment}

上記条件で、${topic}に関する${getTypeLabel(type)}を指定のJSON形式で生成してください。`;

  let json;
  if (!getApiKey()) {
    await new Promise(r => setTimeout(r, 1500));
    json = generateDemo(subject, topic, level);
  } else {
    try {
      // クオリティ最優先: Opus 4.7 を使用。
      // Opus 4.7 は thinking.type='enabled' を拒否するため adaptive + effort を使う。
      // 旧モデル(Sonnet 4.6 以下)は従来通り enabled + budget_tokens。
      const isOpus47 = (MODEL_PREMIUM || '').startsWith('claude-opus-4-7');
      const body = {
        model: MODEL_PREMIUM,
        max_tokens: 16000,
        temperature: 1.0,
        system: systemPrompt,
        messages: [{ role: 'user', content: userMsg }],
      };
      if (isOpus47) {
        body.thinking = { type: 'adaptive' };
        body.output_config = { effort: 'high' };  // 教材生成は高 effort 固定
      } else {
        body.thinking = { type: 'enabled', budget_tokens: 5000 };
      }
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': getApiKey(),
          'anthropic-version': '2023-06-01',
          'anthropic-dangerous-direct-browser-access': 'true'
        },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const errText = await res.text();
        throw new Error(`API ${res.status}: ${errText.slice(0, 200)}`);
      }
      const data = await res.json();
      // Extended Thinking有効時、contentには複数のブロックが返る（thinking + text）
      // text block を見つけてパース
      const textBlock = (data.content || []).find(b => b.type === 'text');
      const text = textBlock?.text || '{}';
      // Strip markdown code fences if present
      const clean = text.trim().replace(/^```(?:json)?\s*\n?/, '').replace(/\n?```\s*$/, '');
      json = JSON.parse(clean);
    } catch (e) {
      alert(`エラー: ${e.message}\nデモ応答を表示します。`);
      json = generateDemo(subject, topic, level);
    }
  }

  lastData = json;
  lastHtml = renderHTML(json);
  lastMd = renderMarkdown(json);
  lastPython = renderPython(json);

  renderView('rendered');
  actions.style.display = 'flex';
  tabs.style.display = 'flex';
  btn.disabled = false;
  btn.textContent = '✨ テキスト教材を生成';
}

function getTypeLabel(type) {
  return {
    full_textbook: '総合テキスト',
    unit_lesson: '単元レッスン',
    exam_package: '模擬試験パッケージ',
    vocab_list: '語彙集',
    reading_set: '長文読解セット',
    worksheet: 'ワークシート',
  }[type] || 'テキスト教材';
}

// ==========================================================================
// Demo response — 科目別に具体的なコンテンツを返す
// ==========================================================================
function generateDemo(subject, topic, level) {
  const sub = String(subject || '');
  const tp = String(topic || '');

  // 古文
  if (/古文/.test(sub) || /敬語|助動詞|源氏|枕草子|徒然草|古文/.test(tp)) {
    return demoKobun(subject, topic, level);
  }
  // 英語
  if (/英語|英検/.test(sub) || /関係代名詞|仮定法|時制|英文法|英単語/.test(tp)) {
    return demoEnglish(subject, topic, level);
  }
  // 数学
  if (/数学/.test(sub) || /2次関数|方程式|三角比|微分|積分|ベクトル|数列/.test(tp)) {
    return demoMath(subject, topic, level);
  }
  // 日本史
  if (/日本史/.test(sub) || /縄文|弥生|平安|鎌倉|江戸|明治|昭和/.test(tp)) {
    return demoNihonshi(subject, topic, level);
  }
  // 物理
  if (/物理/.test(sub) || /運動方程式|等加速度|エネルギー|波動/.test(tp)) {
    return demoPhysics(subject, topic, level);
  }
  // 化学
  if (/化学/.test(sub) || /モル|酸化還元|中和/.test(tp)) {
    return demoChemistry(subject, topic, level);
  }
  // 生物
  if (/生物/.test(sub) || /細胞|DNA|遺伝|光合成|免疫/.test(tp)) {
    return demoBiology(subject, topic, level);
  }
  // フォールバック: 汎用
  return demoGeneric(subject, topic, level);
}

function demoGeneric(subject, topic, level) {
  return {
    title: `${topic} 完全マスター`,
    subtitle: `${level} ${subject}`,
    subject, topic, level,
    sections: [
      {
        type: 'intro', heading: 'はじめに',
        body: `${topic}は${subject}の中でも特に重要な単元の一つです。この教材では、${level}レベルを想定し、基本から応用まで段階的に理解を深めていきます。\n\n単に暗記するのではなく、「なぜそうなるのか」という原理から理解することで、初見の問題にも対応できる真の実力が身につきます。`
      },
      {
        type: 'theory', heading: '基本事項',
        body: `${topic}を理解するためには、まず以下の3つの要素を押さえることが重要です。\n\n1. 定義と基本原理\n2. 他の単元との関連性\n3. 典型的な出題パターン\n\n特に定義は、問題を見たときの「型」を作る土台となります。`,
        table: [['観点', '従来の覚え方', 'この教材での理解'], ['定義', '丸暗記', '原理から理解'], ['応用', 'パターン暗記', 'メカニズムから推論']]
      },
      {
        type: 'tip', title: '攻略のコツ',
        body: `${topic}で最も重要なのは「問題を見たら何をするか」の順序を決めることです。\n\n・ 何が問われているかを見極める\n・ 使える公式・定理を3つに絞る\n・ 最も計算が楽な方法から試す`
      },
      {
        type: 'warn', title: 'よくあるミス',
        body: `${topic}でミスしやすいポイント:\n\n・ 条件を見落として一般化しすぎる\n・ 計算は合っているが、問いに答えていない\n・ 部分点狙いで複数解法を混ぜて書く`
      },
      {
        type: 'example', number: 1,
        question: `${topic}に関する典型問題その1。【問題文がここに入る】`,
        thought: `まず問題文を読んで、何が問われているかを特定します。\n\nステップ1: 与えられた条件を整理する\nステップ2: 使える公式・定理を検討する\nステップ3: 最も効率的な解法を選ぶ\n\n今回の問題では、〇〇法が有効です。理由は...（思考プロセス詳細）`,
        answer: `答え：【模範解答】`,
        explanation: `この問題のポイントは、条件の〇〇に気づけるかどうかです。もし気づけなければ、△△の手順で試行錯誤することになり、時間を浪費します。\n\n次回同じタイプの問題に出会ったら、まず〇〇を確認する癖をつけましょう。`
      },
      {
        type: 'example', number: 2,
        question: `${topic}の応用問題。【問題文がここに入る】`,
        thought: `基礎問題とは異なり、この応用問題では複数のアプローチを組み合わせる必要があります。`,
        answer: `答え：【応用問題の解答】`,
        explanation: `応用問題では、基礎の組合せ方が試されます。典型的な組合せパターンは...`
      },
      {
        type: 'practice', number: 1,
        question: `【演習問題1】 ${topic}の基本確認問題。ここに問題文。`
      },
      {
        type: 'practice', number: 2,
        question: `【演習問題2】 ${topic}の応用問題。ここに問題文。`
      },
      {
        type: 'practice', number: 3,
        question: `【演習問題3】 ${topic}の発展問題。ここに問題文。`
      },
      {
        type: 'answer', number: 1,
        answer: '解答1',
        explanation: '演習1の解説...'
      },
      {
        type: 'answer', number: 2,
        answer: '解答2',
        explanation: '演習2の解説...'
      },
      {
        type: 'answer', number: 3,
        answer: '解答3',
        explanation: '演習3の解説...'
      },
      {
        type: 'summary', heading: 'まとめ',
        points: [
          `${topic}の定義と基本原理を理解する`,
          `よく使う公式・定理を3つ覚える`,
          `典型問題のパターンを5つ押さえる`,
          `応用問題は基礎の組合せで解く`,
          `次のステップは〇〇の学習`
        ]
      }
    ]
  };
}

// 古文 デモ
function demoKobun(subject, topic, level) {
  return {
    title: `古文 ${topic} 完全攻略`,
    subtitle: `${level} — 敬語・助動詞の盤石な理解で読解力を底上げ`,
    subject, topic, level,
    sections: [
      { type: 'intro', heading: 'はじめに', body: `古文は「暗号を解く」行為ではなく、現代日本語の祖先を読む活動です。${topic}を理解すれば、『源氏物語』『徒然草』『枕草子』といった名作が一気に読めるようになります。\n\nこの教材では、文法規則を丸暗記させるのではなく「なぜその活用/意味になるのか」の原理から解説します。古文単語300語+助動詞表+敬語の三本柱を押さえれば、センター古文は8割、二次試験でも合格ラインに達します。` },
      { type: 'theory', heading: '基本事項', body: `【敬語の三分類】\n1. 尊敬語: 動作の主体を敬う（給ふ・のたまふ・おはす）\n2. 謙譲語: 動作の対象（目的語）を敬う（奉る・聞こゆ・参る）\n3. 丁寧語: 聞き手・読み手を敬う（侍り・候ふ）\n\n【敬意の方向】\n地の文: 筆者 → 作中人物\n会話文: 話者 → 聞き手/話題の人物`, table: [['種類','代表語','敬意の対象'],['尊敬語','給ふ・のたまふ','動作主'],['謙譲語','奉る・参る','動作の目的語'],['丁寧語','侍り・候ふ','聞き手']] },
      { type: 'tip', title: '給ふの見分け方', body: `「給ふ」は四段活用なら尊敬（「お〜になる」）、下二段活用なら謙譲（「〜させていただく」）。活用形で意味が決まる珍しい敬語の代表例。\n- 四段: 給は・給ひ・給ふ・給ふ・給へ・給へ（尊敬）\n- 下二段: 給へ・給へ・給ふ・給ふる・給ふれ・給へよ（謙譲）` },
      { type: 'warn', title: 'よくあるミス', body: `1. 主語を取り違える: 敬語の「方向」を頼りにすれば主語が特定できる\n2. 二重敬語を見落とす: 「せさせ給ふ」は皇族級にのみ使う最高敬語\n3. 「す・さす」を使役と決めつける: 尊敬の用法もある（「仰す」「聞こしめす」）` },
      { type: 'example', number: 1, question: '次の傍線部「給ふ」の敬語の種類を答えなさい。\n\n「かぐや姫、いといたく泣き給ふ。」', thought: 'まず活用を確認。「給ふ」は四段活用の終止形。四段の「給ふ」は尊敬語。\n次に敬意の対象。地の文での尊敬語 → 筆者から動作主への敬意。動作主は「かぐや姫」。', answer: '尊敬語／敬意の対象: かぐや姫（動作主）', explanation: '四段活用の「給ふ」は本動詞としても補助動詞としても尊敬の意を表す。ここでは「泣く」に接続する補助動詞として機能している。地の文なので、筆者（作者）→かぐや姫への敬意。' },
      { type: 'example', number: 2, question: '次の文の敬語「奉る」の種類を答え、現代語訳しなさい。\n\n「中納言、扇を帝に奉り給ふ。」', thought: '「奉る」は謙譲語「与ふ」の謙譲語。目的語（扇を受け取る人＝帝）への敬意。\n「給ふ」は尊敬補助動詞 → 動作主「中納言」への敬意。\n訳すと尊敬と謙譲の両方を反映させる。', answer: '謙譲語／訳: 中納言が、扇を帝に差し上げなさる。', explanation: '一文に尊敬（給ふ）と謙譲（奉る）が共存する典型例。中納言は筆者から敬意を受ける存在だが、帝に対しては臣下なので、動作自体は謙譲で表現される。' },
      { type: 'practice', number: 1, question: '次の傍線部の敬語の種類と敬意の対象を答えなさい。\n「この女、いと若ければ、文も書かせ給はず。」' },
      { type: 'practice', number: 2, question: '次の文の「侍り」の敬語分類と現代語訳を答えなさい。\n「御前に人多く侍り。」' },
      { type: 'practice', number: 3, question: '次の文に含まれる二重敬語を指摘し、その敬意の対象を答えなさい。\n「帝、物語などせさせ給ふ。」' },
      { type: 'answer', number: 1, answer: '尊敬語／敬意の対象: この女（動作主）', explanation: '「せ」は使役・尊敬の助動詞「す」の未然形、「給は」は尊敬補助動詞。「書かせ給ふ」で二重敬語とまでは言えないが、尊敬が重なる形。若い女性に対して使われており、身分の高い女性と推察できる。' },
      { type: 'answer', number: 2, answer: '丁寧語／訳: 御前に人が多くおります。', explanation: '「侍り」は「あり」「をり」の丁寧語。聞き手への敬意を示す。対話の場面でのみ使う敬語で、地の文ではあまり使わない。' },
      { type: 'answer', number: 3, answer: '二重敬語: 「せさせ給ふ」／敬意の対象: 帝', explanation: '「せ」(尊敬) + 「させ」(尊敬) + 「給ふ」(尊敬) の三重構造とも解釈されるが、一般的には「せさせ給ふ」で二重敬語（最高敬語）とされる。天皇や皇族にのみ用いる。' },
      { type: 'summary', heading: 'まとめ', points: [
        '敬語は「尊敬・謙譲・丁寧」の三分類',
        '敬意の方向: 地の文=筆者から、会話文=話者から',
        '給ふは活用で意味が決まる（四段=尊敬、下二段=謙譲）',
        '二重敬語「せさせ給ふ」は皇族級にのみ使用',
        '主語が省略された時は敬語の方向から特定する'
      ]}
    ]
  };
}

// 英語 デモ
function demoEnglish(subject, topic, level) {
  return {
    title: `英語 ${topic} 徹底攻略`,
    subtitle: `${level} — 入試英語で差がつく理解の型`,
    subject, topic, level,
    sections: [
      { type: 'intro', heading: 'はじめに', body: `${topic}は英文読解・英作文どちらでも頻出の重要単元です。「ルールを暗記する」のではなく「英語話者がなぜその表現を選ぶのか」を理解することで、応用力が飛躍的に伸びます。\n\nこの教材では、文法の核となるイメージを掴み、例文→類題→応用で段階的に定着させます。` },
      { type: 'theory', heading: '基本事項', body: `関係代名詞は「2つの文を1つにまとめる接着剤」。先行詞（まとめる対象となる名詞）と、関係詞節の中での役割（主格/目的格/所有格）で使い分けます。\n\n- 先行詞が人: who / whom / whose\n- 先行詞がモノ: which / whose\n- 両方可: that`, table: [['格','人','モノ','省略'],['主格','who','which','不可'],['目的格','whom/who','which','可'],['所有格','whose','whose','不可']] },
      { type: 'tip', title: '見抜き方のコツ', body: `関係代名詞の後に「動詞」が来れば主格、「主語+動詞」が来れば目的格。目的格は省略できるので、連続する名詞句を見たら「関係代名詞が省略されてるのでは？」と疑う癖をつけよう。\n\n例: The book (which) I bought yesterday is interesting.\n→ (which) は目的格なので省略可能。` },
      { type: 'warn', title: 'よくあるミス', body: `1. 二重目的語: 関係代名詞 which/that が既に目的語の役割 → 元の it/him を残してしまう\n   ×: The book that I bought **it** is interesting.\n   ○: The book that I bought is interesting.\n\n2. 前置詞 + that: in that / at that は不可。in which / at which にする\n3. the only/最上級の後は that が自然` },
      { type: 'example', number: 1, question: '空所に入る関係代名詞を選びなさい。\n\nThe book ( ) I borrowed from the library was very interesting.\n(a) who (b) which (c) what (d) whose', thought: '先行詞 "the book" は「モノ」→ which か that。\n関係節内で which は borrowed の目的語 → 目的格。\n選択肢に that がないので (b) which が正答。', answer: '(b) which', explanation: '先行詞が人なら who/whom、モノなら which、両方可なら that。目的格なので省略しても文が成立する: "The book I borrowed from the library..."' },
      { type: 'example', number: 2, question: '次の2文を関係代名詞でつなぎなさい。\n\nThis is the teacher. He taught me English last year.', thought: '2文目の He は 1文目の the teacher を指している。He は主格（taught の主語）→ 主格の関係代名詞。\n先行詞が人なので who (or that)。', answer: 'This is the teacher who (or that) taught me English last year.', explanation: '主格の関係代名詞は省略不可。先行詞が人なら who を優先するが、that も正しい。口語では that の方が自然なこともある。' },
      { type: 'practice', number: 1, question: '空所補充: She is the only person ( ) can solve this problem.' },
      { type: 'practice', number: 2, question: '書き換え: This is the house. My grandfather lived in it. → 関係代名詞を使って1文に。' },
      { type: 'practice', number: 3, question: '誤文訂正: I like the song that you were singing it yesterday.' },
      { type: 'answer', number: 1, answer: 'that', explanation: 'the only / 最上級 / every / all などに限定される先行詞の後は that が好まれる。who も文法的には可だが、that がベター。' },
      { type: 'answer', number: 2, answer: 'This is the house which my grandfather lived in. (または: This is the house in which my grandfather lived.)', explanation: '前置詞の位置で2パターン。① 文末に残す（口語的）② 関係代名詞の前に移動（フォーマル）。②の場合 that は不可。' },
      { type: 'answer', number: 3, answer: 'I like the song that you were singing yesterday. (it を削除)', explanation: 'that が既に sing の目的語の役割を持っているので、it は不要。関係代名詞節では先行詞を指す代名詞を重複させてはいけない。' },
      { type: 'summary', heading: 'まとめ', points: [
        '先行詞の種類（人/モノ）と関係節内での役割（主格/目的格）で使い分け',
        '目的格は省略可、主格は省略不可',
        '前置詞 + that は不可（in which が正しい）',
        'the only/最上級の後は that が自然',
        '重複代名詞（it/him）を残さない'
      ]}
    ]
  };
}

// 数学 デモ
function demoMath(subject, topic, level) {
  return {
    title: `数学 ${topic} 徹底理解`,
    subtitle: `${level} — 典型問題と思考プロセス`,
    subject, topic, level,
    sections: [
      { type: 'intro', heading: 'はじめに', body: `${topic}は数学の中でも特に重要な単元で、入試頻出です。この教材では「解き方の発想」から丁寧に解説し、なぜその解法を選ぶのかを明確にします。\n\n暗記では対応できない応用問題にも、典型パターンの組合せで対処できるようになります。` },
      { type: 'theory', heading: '基本事項', body: `2次関数 y = ax² + bx + c の性質:\n- a > 0 なら下に凸、a < 0 なら上に凸\n- 頂点は平方完成で求める: y = a(x-p)² + q なら頂点 (p, q)\n- 軸は x = p、最大値/最小値は q`, table: [['形式','頂点','軸'],['y=ax²+bx+c','(-b/2a, c-b²/4a)','x=-b/2a'],['y=a(x-p)²+q','(p, q)','x=p']] },
      { type: 'tip', title: '平方完成のコツ', body: `y = 2x² - 8x + 5 を平方完成する手順:\n1. x²の係数で x² と x の項をくくる: y = 2(x² - 4x) + 5\n2. (x-2)²の形を作る: y = 2((x-2)² - 4) + 5\n3. 展開して整理: y = 2(x-2)² - 3\n→ 頂点 (2, -3)` },
      { type: 'warn', title: 'よくあるミス', body: `1. くくり忘れ: x²の係数 a を忘れて平方完成 → 頂点がズレる\n2. 符号ミス: (x-p)² の展開時の符号確認\n3. 定義域の見落とし: 最大/最小を求める際、定義域に注意` },
      { type: 'example', number: 1, question: '2次関数 y = x² - 4x + 3 の頂点と軸を求めなさい。', thought: '平方完成の基本形 y = (x-p)² + q にする。\ny = x² - 4x + 3\n= (x-2)² - 4 + 3\n= (x-2)² - 1\nこれで頂点と軸が即座に分かる。', answer: '頂点 (2, -1)、軸 x = 2', explanation: '平方完成により、頂点の座標と軸が一目で分かる。グラフを描く際は、頂点・軸・y切片(x=0のとき y=3)を押さえれば正確に描ける。' },
      { type: 'example', number: 2, question: '関数 f(x) = x² + 2x + a の最小値が 3 のとき、a の値を求めなさい。', thought: '最小値を求めるには平方完成。\nf(x) = (x+1)² - 1 + a = (x+1)² + (a-1)\n最小値は (x+1)² = 0 のとき、すなわち a-1\n→ a - 1 = 3', answer: 'a = 4', explanation: '平方完成の形 (x-p)² + q から、最小値は q = a-1 と読み取れる。問題文の条件「最小値が3」と照合して a = 4。' },
      { type: 'practice', number: 1, question: '2次関数 y = -x² + 6x - 5 の頂点と最大値を求めなさい。' },
      { type: 'practice', number: 2, question: '不等式 x² - 5x + 6 > 0 を解きなさい。' },
      { type: 'practice', number: 3, question: '2次関数 y = x² + 2x + 3 のグラフを -2 ≤ x ≤ 1 の範囲で描き、最大値・最小値を求めなさい。' },
      { type: 'answer', number: 1, answer: '頂点 (3, 4)、最大値 4', explanation: 'y = -(x-3)² + 4。上に凸 (a<0) なので頂点が最大値を与える。' },
      { type: 'answer', number: 2, answer: 'x < 2 または x > 3', explanation: '(x-2)(x-3) > 0 に因数分解。積が正 → 両方正 or 両方負 → x<2 or x>3。' },
      { type: 'answer', number: 3, answer: '最大値 6 (x=1)、最小値 2 (x=-1)', explanation: 'y = (x+1)² + 2 より頂点 (-1, 2) で最小。定義域の端 x=-2, x=1 での値を比較し、x=1 で y=6 が最大。' },
      { type: 'summary', heading: 'まとめ', points: [
        '2次関数は常に平方完成して頂点と軸を把握',
        'a の符号で凸の向きが決まる',
        '最大最小は定義域の端と頂点の比較',
        '不等式は因数分解して数直線で判定',
        '判別式 D = b²-4ac で解の個数が分かる'
      ]}
    ]
  };
}

// 日本史 デモ
function demoNihonshi(subject, topic, level) {
  return {
    title: `日本史 ${topic} 完全理解`,
    subtitle: `${level} — 流れと因果で掴む`,
    subject, topic, level,
    sections: [
      { type: 'intro', heading: 'はじめに', body: `${topic}の学習では、単なる年号暗記ではなく「なぜその出来事が起きたか」という因果関係の理解が重要です。\n\nこの教材では、時代の流れ、政治・経済・文化の相互関係、そして入試で問われるポイントを体系的に学びます。` },
      { type: 'theory', heading: '基本事項', body: `原始・古代の区分:\n- 旧石器時代: 打製石器、狩猟採集\n- 縄文時代: 磨製石器、縄文土器、竪穴住居\n- 弥生時代: 稲作伝来、金属器、クニの成立\n- 古墳時代: 前方後円墳、大和政権\n- 飛鳥時代: 仏教伝来、聖徳太子の政治\n- 奈良時代: 律令国家、天平文化\n- 平安時代: 摂関政治、国風文化、院政`, table: [['時代','年代','特徴'],['縄文','前1万年〜前4世紀','採集経済'],['弥生','前4世紀〜後3世紀','稲作社会'],['古墳','3〜7世紀','統一政権'],['飛鳥','592〜710','仏教受容']] },
      { type: 'tip', title: '年号記憶のコツ', body: `単独の数字は忘れやすい。「出来事の因果」とセットで覚える:\n- 645年 乙巳の変: 蘇我氏滅亡 → 大化の改新（公地公民）\n- 710年 平城京遷都: 律令国家の本格始動\n- 743年 墾田永年私財法: 公地公民の崩壊 → 荘園の起源\n- 794年 平安京遷都: 桓武天皇の律令再建\n- 894年 遣唐使廃止: 国風文化の始まり` },
      { type: 'warn', title: 'よくあるミス', body: `1. 似た名前の混同: 蘇我入鹿 vs 蘇我馬子、中大兄皇子 vs 中臣鎌足\n2. 年代の取り違え: 飛鳥時代の始まり（592年 vs 593年 vs 聖徳太子の摂政開始）\n3. 文化の担い手の混同: 天平文化（貴族・仏教）vs 国風文化（貴族・和風）` },
      { type: 'example', number: 1, question: '大化の改新（645年）の中心人物2名と、彼らが打倒した氏族を答えなさい。', thought: '645年の乙巳の変→大化の改新。\n中心人物: 中大兄皇子（後の天智天皇）+ 中臣鎌足（後の藤原鎌足）\n打倒した氏族: 蘇我氏（入鹿を暗殺、蝦夷自殺）', answer: '中心人物: 中大兄皇子、中臣鎌足／打倒した氏族: 蘇我氏', explanation: '蘇我氏は仏教受容を主導して権勢を振るっていたが、聖徳太子死後に専横化。中大兄皇子と中臣鎌足は645年に宮中で入鹿を暗殺（乙巳の変）。翌年から公地公民・班田収授法などの大化の改新が始まる。' },
      { type: 'example', number: 2, question: '墾田永年私財法（743年）の内容と、それが日本の土地制度にもたらした影響を述べなさい。', thought: '743年、聖武天皇の時代。三世一身法（723年）で土地を一時的に私有化できたが、開墾が進まないため永年私財に。\n→ 結果として、公地公民が崩れ、有力貴族・大寺社による土地囲い込みが進行 → 荘園の起源。', answer: '内容: 新たに開墾した土地の永代私有を認めた法令。\n影響: 公地公民制の崩壊、荘園の発生、律令国家の根幹が揺らぐ。', explanation: '口分田不足を補うため開墾を奨励する狙いだったが、結果として有力者の土地集積が進み、平安時代の荘園制へと発展。律令制度の崩壊の起点となった。' },
      { type: 'practice', number: 1, question: '弥生時代に大陸から伝来した技術・文化を3つ挙げなさい。' },
      { type: 'practice', number: 2, question: '聖徳太子の政治の内容を3点以上挙げなさい。' },
      { type: 'practice', number: 3, question: '平安時代の「国風文化」の特徴と代表作を挙げなさい。' },
      { type: 'answer', number: 1, answer: '稲作（水稲耕作）、金属器（青銅器・鉄器）、機織り技術', explanation: '朝鮮半島経由で伝来。稲作は社会構造を変革し、貧富の差・集落の階層化・クニの発生をもたらした。' },
      { type: 'answer', number: 2, answer: '1. 冠位十二階の制定（603年）- 氏族序列を個人の実力評価に\n2. 憲法十七条（604年）- 官人の心得を定める\n3. 遣隋使派遣 - 小野妹子を派遣、対等外交を試みる\n4. 法隆寺建立 - 仏教文化の中心', explanation: '蘇我氏との協調のもと、中央集権国家への転換を図った。仏教受容も進めた。' },
      { type: 'answer', number: 3, answer: '特徴: 唐風から日本独自の文化へ転換、仮名文字の発達、和歌・物語文学の興隆。\n代表作: 『源氏物語』(紫式部)、『枕草子』(清少納言)、『古今和歌集』(紀貫之ら)', explanation: '894年の遣唐使廃止を契機に、日本独自の感性で文化を昇華させた。貴族の女性が中心となった点が特徴的。' },
      { type: 'summary', heading: 'まとめ', points: [
        '縄文→弥生で農耕社会へ、古墳→飛鳥で統一国家へ',
        '律令国家の完成: 大宝律令(701年)',
        '墾田永年私財法(743年)が公地公民崩壊の起点',
        '国風文化: 894年の遣唐使廃止以降',
        '年号は「出来事と因果」のセットで記憶'
      ]}
    ]
  };
}

// 物理 デモ（簡略）
function demoPhysics(subject, topic, level) {
  return {
    title: `物理 ${topic} 徹底理解`, subtitle: `${level}`, subject, topic, level,
    sections: [
      { type: 'intro', heading: 'はじめに', body: `物理は「現象 → 法則 → 式」の順で理解することが鉄則です。公式を丸暗記するのではなく、なぜその式が成り立つかを納得しながら進めましょう。` },
      { type: 'theory', heading: '基本事項', body: `等加速度直線運動の3公式:\n- v = v₀ + at\n- x = v₀t + (1/2)at²\n- v² - v₀² = 2ax\n運動方程式: ma = F` },
      { type: 'example', number: 1, question: '初速 10 m/s で右向きに進む物体に、加速度 2 m/s² を加えた。5秒後の速度と位置を求めよ。', thought: 'v = v₀ + at、x = v₀t + at²/2 を使う。', answer: 'v = 20 m/s、x = 75 m', explanation: 'v = 10 + 2×5 = 20。x = 10×5 + (1/2)×2×25 = 50 + 25 = 75。' },
      { type: 'practice', number: 1, question: '質量 2 kg の物体に 6 N の力を加えた。加速度は？' },
      { type: 'answer', number: 1, answer: '3 m/s²', explanation: 'ma = F → a = F/m = 6/2 = 3。' },
      { type: 'summary', heading: 'まとめ', points: ['3公式は等加速度運動の核', 'ma = F は力学の基本', '単位(MKS)に注意'] }
    ]
  };
}

// 化学 デモ（簡略）
function demoChemistry(subject, topic, level) {
  return {
    title: `化学 ${topic} 完全攻略`, subtitle: `${level}`, subject, topic, level,
    sections: [
      { type: 'intro', heading: 'はじめに', body: `化学は「モル」を中心に体系化されています。n = w/M = V/22.4(気体) = c×V(溶液) の三位一体を押さえれば、多くの問題が解けます。` },
      { type: 'theory', heading: '基本事項', body: `モル計算の核:\n- 質量基準: n = w / M（M=分子量）\n- 気体基準: n = V / 22.4（標準状態、0℃ 1気圧）\n- 溶液基準: n = c × V（c=モル濃度）\nアボガドロ定数: Nₐ = 6.0×10²³` },
      { type: 'example', number: 1, question: '水 H₂O 18g は何モルか、また何分子か。', thought: 'H₂O の分子量 = 18。n = 18/18 = 1。分子数 = 1 × 6.0×10²³。', answer: '1 mol、6.0×10²³ 分子', explanation: 'モル数 × アボガドロ定数で分子数が求まる。' },
      { type: 'practice', number: 1, question: '0.1 mol/L の塩酸 100 mL を中和するのに、0.2 mol/L NaOH 水溶液は何 mL 必要か。' },
      { type: 'answer', number: 1, answer: '50 mL', explanation: 'c₁V₁ = c₂V₂ → 0.1×100 = 0.2×V → V = 50。' },
      { type: 'summary', heading: 'まとめ', points: ['モル計算の三位一体', '中和は c₁V₁ = c₂V₂', 'イオン化傾向を暗記'] }
    ]
  };
}

// 生物 デモ（簡略）
function demoBiology(subject, topic, level) {
  return {
    title: `生物 ${topic} 徹底理解`, subtitle: `${level}`, subject, topic, level,
    sections: [
      { type: 'intro', heading: 'はじめに', body: `生物は「構造 → 機能 → 調節」の3段階で理解します。ただの暗記ではなく、なぜその仕組みが進化的に有利だったかを考えると定着します。` },
      { type: 'theory', heading: '基本事項', body: `セントラルドグマ: DNA → RNA → タンパク質\n- 転写: DNA → mRNA（核内）\n- 翻訳: mRNA → タンパク質（リボソーム）\n真核細胞と原核細胞の違い: 核膜の有無` },
      { type: 'example', number: 1, question: '光合成の化学反応式を完成させなさい: 6CO₂ + 6H₂O + [？] → C₆H₁₂O₆ + 6O₂', thought: '光合成は光エネルギーを化学エネルギー(糖)に変換。', answer: '光エネルギー', explanation: '葉緑体のチラコイドで光を吸収し、ストロマでカルビン回路が回って糖が合成される。' },
      { type: 'practice', number: 1, question: '抗体を産生する細胞を答えなさい。' },
      { type: 'answer', number: 1, answer: 'B細胞（形質細胞に分化して抗体を産生）', explanation: 'ヘルパーT細胞の助けを受けて、B細胞が形質細胞へ分化し抗体を大量生産する。' },
      { type: 'summary', heading: 'まとめ', points: ['真核 vs 原核', 'セントラルドグマ', '光合成は光エネルギーを糖へ', '免疫はB細胞・T細胞'] }
    ]
  };
}

// ==========================================================================
// Renderers
// ==========================================================================
function renderHTML(j) {
  const layout = getLayoutMode();
  let html = `<h1>${escapeHtml(j.title)}</h1>\n`;
  if (j.subtitle) html += `<p style="color:#6b7280;font-size:1.05rem;margin-top:-1rem;margin-bottom:2rem;">${escapeHtml(j.subtitle)}</p>\n`;

  const sections = j.sections || [];

  // レイアウトモード別にレンダリング
  if (layout === 'end') {
    // 巻末解答: 問題を全て先に、解答はまとめて最後に
    html += renderProblemsSection(sections, { hideAnswers: true });
    html += renderAnswersAtEnd(sections);
  } else if (layout === 'inline') {
    // 全表示: 従来通り問題直後に解答
    html += renderProblemsSection(sections, { hideAnswers: false });
  } else {
    // hidden (default): 問題直後に「答えを見る」ボタン（クリックで展開）
    html += renderProblemsSection(sections, { hideAnswers: true, collapsible: true });
  }

  return html;
}

function getLayoutMode() {
  const el = document.querySelector('input[name="answerLayout"]:checked');
  return el ? el.value : 'hidden';
}

function renderProblemsSection(sections, opts = {}) {
  const { hideAnswers, collapsible } = opts;
  let html = '';
  let exampleIdx = 0;
  let practiceIdx = 0;

  for (const s of sections) {
    if (s.type === 'intro' || s.type === 'theory') {
      if (s.heading) html += `<h2>${escapeHtml(s.heading)}</h2>\n`;
      html += `<p>${escapeHtml(s.body || '').replace(/\n/g, '<br>')}</p>\n`;
      if (s.table) {
        html += '<table><thead><tr>';
        s.table[0].forEach(th => html += `<th>${escapeHtml(th)}</th>`);
        html += '</tr></thead><tbody>';
        s.table.slice(1).forEach(row => {
          html += '<tr>';
          row.forEach(td => html += `<td>${escapeHtml(td)}</td>`);
          html += '</tr>';
        });
        html += '</tbody></table>\n';
      }
    } else if (s.type === 'tip') {
      html += `<div class="tip-box"><strong>${escapeHtml(s.title || 'ポイント')}</strong><br>${escapeHtml(s.body || '').replace(/\n/g, '<br>')}</div>\n`;
    } else if (s.type === 'warn') {
      html += `<div class="warn-box"><strong>${escapeHtml(s.title || '注意')}</strong><br>${escapeHtml(s.body || '').replace(/\n/g, '<br>')}</div>\n`;
    } else if (s.type === 'example') {
      exampleIdx++;
      const num = s.number || exampleIdx;
      html += `<div class="problem-wrap">
        <div class="problem-title">例題 ${num}</div>
        <div class="problem-body">${escapeHtml(s.question || '').replace(/\n/g, '<br>')}</div>`;

      if (!hideAnswers) {
        // 全表示モード: そのまま解答表示
        if (s.thought) html += `<div style="margin-top:1rem;"><h4 style="color:var(--primary-light);font-size:0.92rem;">💭 解き方の発想</h4><p>${escapeHtml(s.thought).replace(/\n/g, '<br>')}</p></div>`;
        html += `<div style="margin-top:0.75rem;"><h4 style="color:var(--accent);font-size:0.92rem;">📝 解答</h4><p><strong>${escapeHtml(s.answer || '')}</strong></p></div>`;
        if (s.explanation) html += `<div style="margin-top:0.5rem;"><h4 style="color:var(--primary-light);font-size:0.92rem;">📖 解説</h4><p>${escapeHtml(s.explanation).replace(/\n/g, '<br>')}</p></div>`;
      } else if (collapsible) {
        // 答えを隠す（展開ボタン）
        const answerId = `example_ans_${num}`;
        html += `
          <button class="reveal-btn" data-target="${answerId}">
            <span>🙈 まず考えてみよう</span>
            <span class="arrow">▼</span>
          </button>
          <div class="reveal-content" id="${answerId}">`;
        if (s.thought) html += `<div class="reveal-section"><h4>💭 解き方の発想</h4><p>${escapeHtml(s.thought).replace(/\n/g, '<br>')}</p></div>`;
        html += `<div class="reveal-section"><h4>📝 解答</h4><p><strong>${escapeHtml(s.answer || '')}</strong></p></div>`;
        if (s.explanation) html += `<div class="reveal-section"><h4>📖 解説</h4><p>${escapeHtml(s.explanation).replace(/\n/g, '<br>')}</p></div>`;
        html += `</div>`;
      }
      html += `</div>`;
    } else if (s.type === 'practice') {
      practiceIdx++;
      const num = s.number || practiceIdx;
      html += `<div class="problem-wrap">
        <div class="problem-title">演習問題 ${num}</div>
        <div class="problem-body">${escapeHtml(s.question || '').replace(/\n/g, '<br>')}</div>
      </div>`;
    } else if (s.type === 'answer') {
      // answer type は hideAnswers=true の場合スキップ（後で巻末にまとめる）
      // 全表示モードのみここで表示
      if (!hideAnswers) {
        html += `<div class="answer-block">
          <div class="answer-block-title">💡 演習${s.number || ''} の解答</div>
          <p><strong>答え:</strong> ${escapeHtml(s.answer || '')}</p>`;
        if (s.explanation) html += `<p style="margin-top:0.5rem;">${escapeHtml(s.explanation).replace(/\n/g, '<br>')}</p>`;
        html += `</div>`;
      }
    } else if (s.type === 'vocab') {
      html += `<h2>重要語彙</h2>\n<table><thead><tr><th>単語</th><th>意味</th><th>例文</th></tr></thead><tbody>`;
      (s.items || []).forEach(i => {
        html += `<tr><td><strong>${escapeHtml(i.word||'')}</strong></td><td>${escapeHtml(i.meaning||'')}</td><td>${escapeHtml(i.example||'')}</td></tr>`;
      });
      html += `</tbody></table>\n`;
    } else if (s.type === 'summary') {
      html += `<h2>${escapeHtml(s.heading || 'まとめ')}</h2>\n<ul>`;
      (s.points || []).forEach(p => html += `<li>${escapeHtml(p)}</li>`);
      html += `</ul>\n`;
    }
  }
  return html;
}

function renderAnswersAtEnd(sections) {
  // 巻末解答モード: 全例題・演習の解答をまとめて最後に表示
  let html = `<div class="answers-section-start">
    <h2>📖 解答・解説編</h2>
    <p>※ ここから先は答え合わせ用。問題を解いてから読みましょう。</p>
  </div>`;

  let exampleIdx = 0;
  let practiceIdx = 0;

  for (const s of sections) {
    if (s.type === 'example') {
      exampleIdx++;
      const num = s.number || exampleIdx;
      html += `<div class="answer-block">
        <div class="answer-block-title">例題 ${num} の解答</div>`;
      if (s.thought) html += `<div class="reveal-section"><h4>💭 解き方の発想</h4><p>${escapeHtml(s.thought).replace(/\n/g, '<br>')}</p></div>`;
      html += `<div class="reveal-section"><h4>📝 解答</h4><p><strong>${escapeHtml(s.answer || '')}</strong></p></div>`;
      if (s.explanation) html += `<div class="reveal-section"><h4>📖 解説</h4><p>${escapeHtml(s.explanation).replace(/\n/g, '<br>')}</p></div>`;
      html += `</div>`;
    } else if (s.type === 'answer') {
      practiceIdx++;
      const num = s.number || practiceIdx;
      html += `<div class="answer-block">
        <div class="answer-block-title">演習問題 ${num} の解答</div>
        <p><strong>答え:</strong> ${escapeHtml(s.answer || '')}</p>`;
      if (s.explanation) html += `<p style="margin-top:0.5rem;">${escapeHtml(s.explanation).replace(/\n/g, '<br>')}</p>`;
      html += `</div>`;
    }
  }
  return html;
}

// Reveal button binding (event delegation)
function bindRevealButtons() {
  const container = document.getElementById('tbResult');
  if (!container) return;
  container.querySelectorAll('.reveal-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const target = document.getElementById(btn.dataset.target);
      if (!target) return;
      const showing = target.classList.toggle('show');
      btn.classList.toggle('expanded', showing);
      btn.querySelector('span').textContent = showing ? '✨ 答えを表示中' : '🙈 まず考えてみよう';
    });
  });
}

function revealAll(show) {
  const container = document.getElementById('tbResult');
  container.querySelectorAll('.reveal-content').forEach(el => {
    el.classList.toggle('show', show);
  });
  container.querySelectorAll('.reveal-btn').forEach(btn => {
    btn.classList.toggle('expanded', show);
    const span = btn.querySelector('span');
    if (span) span.textContent = show ? '✨ 答えを表示中' : '🙈 まず考えてみよう';
  });
}

function renderMarkdown(j) {
  let md = `# ${j.title}\n\n`;
  if (j.subtitle) md += `*${j.subtitle}*\n\n---\n\n`;

  for (const s of j.sections || []) {
    if (s.type === 'intro' || s.type === 'theory') {
      if (s.heading) md += `## ${s.heading}\n\n`;
      md += `${s.body}\n\n`;
      if (s.table) {
        md += s.table[0].map(c => `| ${c} `).join('') + '|\n';
        md += s.table[0].map(() => '|---').join('') + '|\n';
        s.table.slice(1).forEach(row => {
          md += row.map(c => `| ${c} `).join('') + '|\n';
        });
        md += '\n';
      }
    } else if (s.type === 'tip') {
      md += `> **💡 ${s.title || 'ポイント'}**\n> ${s.body?.replace(/\n/g, '\n> ') || ''}\n\n`;
    } else if (s.type === 'warn') {
      md += `> **⚠️ ${s.title || '注意'}**\n> ${s.body?.replace(/\n/g, '\n> ') || ''}\n\n`;
    } else if (s.type === 'example') {
      md += `### 例題${s.number || ''}\n\n**問題:** ${s.question || ''}\n\n`;
      if (s.thought) md += `#### 解き方の発想\n${s.thought}\n\n`;
      md += `#### 解答\n**${s.answer || ''}**\n\n`;
      if (s.explanation) md += `#### 解説\n${s.explanation}\n\n`;
    } else if (s.type === 'practice') {
      md += `### 演習${s.number || ''}\n${s.question || ''}\n\n`;
    } else if (s.type === 'answer') {
      md += `### 解答${s.number || ''}\n**答え:** ${s.answer || ''}\n\n${s.explanation || ''}\n\n`;
    } else if (s.type === 'vocab') {
      md += `## 重要語彙\n\n| 単語 | 意味 | 例文 |\n|---|---|---|\n`;
      (s.items || []).forEach(i => {
        md += `| **${i.word||''}** | ${i.meaning||''} | ${i.example||''} |\n`;
      });
      md += '\n';
    } else if (s.type === 'summary') {
      md += `## ${s.heading || 'まとめ'}\n\n`;
      (s.points || []).forEach(p => md += `- ${p}\n`);
      md += '\n';
    }
  }
  return md;
}

function renderPython(j) {
  return `# ==========================================================================
# 自動生成されたテキスト教材データ
# 教材: ${j.title}
# ==========================================================================
# 使い方:
# 1. eiken_pre1_textbook.py / kobun_textbook.py 内の CHAPTERS 変数を
#    この配列で置換
# 2. python3 eiken_pre1_textbook.py を実行
# 3. textbook.pdf が生成される

CHAPTERS = [
    {
        "title": ${JSON.stringify(j.title || '')},
        "subtitle": ${JSON.stringify(j.subtitle || '')},
        "sections": [
${(j.sections || []).map(s => '            ' + JSON.stringify(s, null, 2).replace(/\n/g, '\n            ')).join(',\n')}
        ]
    }
]

# 既存のビルド関数がそのまま使える形式になっています。
`;
}

function renderView(view) {
  const el = document.getElementById('tbResult');
  const toolbar = document.getElementById('viewToolbar');
  if (!lastData) return;
  if (view === 'rendered') {
    el.className = 'tb-result rendered';
    // レイアウト切替時に再レンダリング
    lastHtml = renderHTML(lastData);
    el.innerHTML = lastHtml;
    // 展開ボタンをbind
    bindRevealButtons();
    // ツールバー: hidden モードの時だけ表示
    if (toolbar) toolbar.style.display = getLayoutMode() === 'hidden' ? 'flex' : 'none';
  } else if (view === 'markdown') {
    el.className = 'tb-result raw';
    el.innerHTML = `<pre>${escapeHtml(lastMd)}</pre>`;
  } else if (view === 'python') {
    el.className = 'tb-result raw';
    el.innerHTML = `<pre>${escapeHtml(lastPython)}</pre>`;
  } else if (view === 'json') {
    el.className = 'tb-result raw';
    el.innerHTML = `<pre>${escapeHtml(JSON.stringify(lastData, null, 2))}</pre>`;
  }
}

function escapeHtml(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c]));
}

function download(content, filename, mime) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click(); a.remove();
  URL.revokeObjectURL(url);
}

// ==========================================================================
// 過去問対応モード (Textbook Generator)
// ==========================================================================
function initTbPastExamUi() {
  const toggle = document.getElementById('tbPastExamToggle');
  const panel = document.getElementById('tbPastExamPanel');
  const univSel = document.getElementById('tbPastExamUniv');
  const yearSel = document.getElementById('tbPastExamYear');
  const subjSel = document.getElementById('tbPastExamSubject');
  const qSel = document.getElementById('tbPastExamQuestion');
  const preview = document.getElementById('tbPastExamPreview');
  if (!toggle || typeof PAST_EXAMS === 'undefined') return;

  toggle.addEventListener('change', () => {
    panel.style.display = toggle.checked ? 'block' : 'none';
  });

  univSel.innerHTML = '<option value="">-- 大学を選択 --</option>' +
    UNIV_CATEGORIES.map(cat => {
      const opts = cat.univs.map(u =>
        PAST_EXAMS[u] ? `<option value="${u}">${u}</option>` : ''
      ).join('');
      return `<optgroup label="${cat.label}">${opts}</optgroup>`;
    }).join('');

  univSel.addEventListener('change', () => {
    const u = univSel.value;
    if (!u || !PAST_EXAMS[u]) {
      yearSel.innerHTML = '<option value="">-- 先に大学選択 --</option>';
      subjSel.innerHTML = '<option value="">-- 先に大学選択 --</option>';
      qSel.innerHTML = '<option value="">全ての大問</option>';
      yearSel.disabled = subjSel.disabled = qSel.disabled = true;
      preview.style.display = 'none';
      return;
    }
    const years = Object.keys(PAST_EXAMS[u].exams).sort().reverse();
    yearSel.innerHTML = '<option value="">-- 年度を選択 --</option>' +
      years.map(y => `<option value="${y}">${y}年度</option>`).join('');
    yearSel.disabled = false;
    subjSel.innerHTML = '<option value="">-- 科目を選択 --</option>' +
      (PAST_EXAMS[u].subjects || []).map(s => `<option value="${s}">${s}</option>`).join('');
    subjSel.disabled = false;
    qSel.innerHTML = '<option value="">全ての大問</option>';
    qSel.disabled = true;
    preview.style.display = 'none';
  });

  const refresh = () => {
    const u = univSel.value, y = yearSel.value, s = subjSel.value;
    qSel.innerHTML = '<option value="">全ての大問</option>';
    qSel.disabled = true;
    preview.style.display = 'none';
    if (!u || !y || !s) return;
    const problems = getPastExamProblems(u, y, s);
    if (problems.length === 0) {
      preview.innerHTML = `<div class="past-exam-preview-title">⚠️ この年度・科目のメタは未登録</div>
        <p style="margin:0;font-size:0.78rem;color:var(--text-muted);">一般的な${u}の${s}出題傾向で類題教材を生成します。</p>`;
      preview.style.display = 'block';
      return;
    }
    qSel.innerHTML = '<option value="">全ての大問</option>' +
      problems.map(p => `<option value="${p.大問}">大問${p.大問}: ${p.テーマ}</option>`).join('');
    qSel.disabled = false;
    preview.innerHTML = `
      <div class="past-exam-preview-title">📋 ${u} ${y}年度 ${s} の大問構成</div>
      <ul class="past-exam-preview-list">
        ${problems.map(p => `
          <li>
            <strong>大問${p.大問}</strong>: ${p.テーマ}
            <span class="past-exam-preview-meta">${p.配点 ? `${p.配点}点` : ''}${p.時間目安 ? ` / ${p.時間目安}` : ''}${p.学部 ? ` / ${p.学部}学部` : ''}</span>
          </li>
        `).join('')}
      </ul>
      <p style="margin:0.5rem 0 0;font-size:0.72rem;color:var(--text-muted);">
        💡 この傾向を踏襲した<strong style="color:#fde68a;">類題・解説教材</strong>をAIが執筆します
      </p>
    `;
    preview.style.display = 'block';
  };
  yearSel.addEventListener('change', refresh);
  subjSel.addEventListener('change', refresh);
}

// ==========================================================================
// Event bindings
// ==========================================================================
document.addEventListener('DOMContentLoaded', () => {
  updateMode();
  document.getElementById('generateTbBtn').addEventListener('click', generateTextbook);

  // 科目変更で単元チップを再描画
  const subjSelect = document.getElementById('tbSubject');
  subjSelect.addEventListener('change', () => {
    tbSelectedUnits = [];  // 科目変更時はリセット
    renderTbUnits(subjSelect.value);
    updateTbSelectedBar();
  });

  // 過去問対応モードUI初期化
  initTbPastExamUi();
  // 初期表示
  renderTbUnits(subjSelect.value);

  // クリアボタン
  document.getElementById('tbUnitClear').addEventListener('click', clearTbUnits);

  document.querySelectorAll('.view-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.view-tab').forEach(t => t.classList.toggle('active', t === tab));
      renderView(tab.dataset.view);
    });
  });

  // レイアウトモード切替で即時再レンダリング
  document.querySelectorAll('input[name="answerLayout"]').forEach(radio => {
    radio.addEventListener('change', () => {
      if (lastData) renderView('rendered');
    });
  });

  // 一括展開/折りたたみボタン
  const revealBtn = document.getElementById('revealAllBtn');
  const hideBtn = document.getElementById('hideAllBtn');
  if (revealBtn) revealBtn.addEventListener('click', () => revealAll(true));
  if (hideBtn) hideBtn.addEventListener('click', () => revealAll(false));

  document.getElementById('tbCopyMd').addEventListener('click', () => {
    navigator.clipboard.writeText(lastMd).then(() => alert('✅ Markdown をコピーしました'));
  });
  document.getElementById('tbCopyHtml').addEventListener('click', () => {
    navigator.clipboard.writeText(lastHtml).then(() => alert('✅ HTML をコピーしました'));
  });
  document.getElementById('tbCopyPython').addEventListener('click', () => {
    navigator.clipboard.writeText(lastPython).then(() => alert(`✅ Python配列をコピーしました\n\nこれを eiken_pre1_textbook.py / kobun_textbook.py の CHAPTERS に貼り付け、\npython3 スクリプト.py で PDF生成できます。`));
  });
  document.getElementById('tbCopyJson').addEventListener('click', () => {
    navigator.clipboard.writeText(JSON.stringify(lastData, null, 2)).then(() => alert('✅ JSON をコピーしました'));
  });
  document.getElementById('tbPrint').addEventListener('click', () => {
    window.print();
  });
  document.getElementById('tbDownload').addEventListener('click', () => {
    const slug = (lastData?.topic || 'textbook').replace(/[^\w\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]/g, '_');
    download(lastMd, `${slug}.md`, 'text/markdown');
  });
});
