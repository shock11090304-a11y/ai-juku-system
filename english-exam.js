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
      { key: 'reading',   name: 'Reading',   icon: '📖', timeMin: 36, qCount: 10, scoreMax: 30, desc: '学術的長文 1-2 passages、各10問' },
      { key: 'listening', name: 'Listening', icon: '🎧', timeMin: 41, qCount: 14, scoreMax: 30, desc: '講義3-4 + 会話2-3、各5-6問' },
      { key: 'speaking',  name: 'Speaking',  icon: '🎙', timeMin: 17, qCount: 4,  scoreMax: 30, desc: 'Independent 1問 + Integrated 3問 (口頭回答)' },
      { key: 'writing',   name: 'Writing',   icon: '✍️', timeMin: 50, qCount: 2,  scoreMax: 30, desc: 'Integrated (300字程度) + Independent (300語以上)' },
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
      { key: 'r_part7', name: 'Reading Part 7',   icon: '📚', timeMin: 55, qCount: 54, scoreMax: 270, desc: '読解 (1文/2文/3文書式)' },
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
      { key: 'listening', name: 'Listening', icon: '🎧', timeMin: 30, qCount: 40, scoreMax: 9.0, desc: '4セクション (日常会話/モノローグ/学術討論/講義)' },
      { key: 'reading',   name: 'Reading',   icon: '📖', timeMin: 60, qCount: 40, scoreMax: 9.0, desc: '学術的長文3つ・40問 (穴埋め/T-F-NG/見出し選択など)' },
      { key: 'writing',   name: 'Writing',   icon: '✍️', timeMin: 60, qCount: 2,  scoreMax: 9.0, desc: 'Task 1 (グラフ150語) + Task 2 (エッセイ250語)' },
      { key: 'speaking',  name: 'Speaking',  icon: '🎙', timeMin: 14, qCount: 3,  scoreMax: 9.0, desc: 'Part 1-3 (自己紹介/2分スピーチ/ディスカッション)' },
    ],
    topics: ['Climate change', 'Urban planning', 'Education systems', 'Healthcare', 'Technology impact', 'Globalization', 'Social inequality', 'Cultural identity'],
  },
  eiken: {
    id: 'eiken',
    name: '英検',
    flag: '🇯🇵',
    color: '#dc2626',
    scoreMin: 0, scoreMax: 0, scoreUnit: '級',
    grades: [
      { key: 'g1',  name: '1級',     cefr: 'C1', target: '英字新聞・専門書・国連職員レベル' },
      { key: 'gp1', name: '準1級',   cefr: 'B2', target: '海外留学・大学入試特典・社会問題に意見' },
      { key: 'g2',  name: '2級',     cefr: 'B1', target: '高校卒業・海外短期留学・実用英会話' },
      { key: 'gp2', name: '準2級',   cefr: 'A2-B1', target: '高校在学中・大学入試・身近な英会話' },
      { key: 'g3',  name: '3級',     cefr: 'A2', target: '中学卒業・短文/対話の理解' },
      { key: 'g4',  name: '4級',     cefr: 'A1', target: '中学中級・基礎英文の理解' },
      { key: 'g5',  name: '5級',     cefr: 'A1', target: '中学初級・あいさつ/簡単な質問' },
    ],
    sections: [
      { key: 'reading',   name: 'Reading',   icon: '📖', timeMin: 30, qCount: 20, scoreMax: 100, desc: '短文穴埋め + 長文読解 + Eメール読解' },
      { key: 'listening', name: 'Listening', icon: '🎧', timeMin: 25, qCount: 30, scoreMax: 100, desc: '会話 + ナレーション + Real-Life形式' },
      { key: 'writing',   name: 'Writing',   icon: '✍️', timeMin: 30, qCount: 1,  scoreMax: 100, desc: '英作文 (級により語数が異なる)' },
      { key: 'speaking',  name: 'Speaking',  icon: '🎙', timeMin: 7,  qCount: 4,  scoreMax: 100, desc: '二次試験 / 面接 (音読+質問4つ)' },
    ],
    topics: ['Daily life', 'School', 'Travel', 'Environment', 'Technology', 'Health', 'Culture', 'Future plans'],
  },
};

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
function isLiveMode() { return !!getApiKey(); }
function updateModeBadge() {
  const el = document.getElementById('modeIndicator');
  if (!el) return;
  if (isLiveMode()) {
    el.textContent = '🟢 Live (Claude API)';
    el.className = 'ee-mode-badge live';
  } else {
    el.textContent = '🟡 デモモード';
    el.className = 'ee-mode-badge demo';
  }
}

// ==========================================================================
// Claude API 呼び出し (JSON出力強制)
// ==========================================================================
async function callClaudeJson({ system, user, model = MODEL_DEFAULT, maxTokens = 4000 }) {
  const apiKey = getApiKey();
  if (!apiKey) throw new Error('NO_API_KEY');
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
  const data = await res.json();
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
}

function pickExam(examId) {
  const exam = EXAMS[examId];
  if (!exam) return;
  state.examId = examId;
  state.sectionKey = null;

  document.getElementById('examPickSection').style.display = 'none';
  document.getElementById('examDetailSection').style.display = '';
  document.getElementById('examDetailTitle').textContent = `${exam.flag} ${exam.name} 対策`;

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

  // セクションカード生成
  const grid = document.getElementById('sectionGrid');
  grid.innerHTML = '';
  exam.sections.forEach(sec => {
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
  const targetSec = exam.sections.find(s => s.key === 'reading' || s.key === 'r_part5' || s.key === 'l_part1') || exam.sections[0];
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

  const system = `あなたは ${exam.name} の試験対策専門コーチで、過去20年の出題傾向を完全に把握しています。
【厳守】
- 出題形式は ${exam.name} の公式準拠 (${section.name}, ${section.desc})
- 難易度は受験者が ${state.currentLevel || 'B1'} レベル想定
- 設問は本物の試験で出るレベルの英文 (機械翻訳臭NG)
- 解説は日本語で、なぜその選択肢が正解か / なぜ他の選択肢が誤答か を丁寧に説明
- TOEFL/IELTS の Reading は学術的、TOEIC の Reading はビジネス・実務的、英検は級に応じた語彙レベル
- Speaking/Writing は採点ルーブリック (構成/語彙/文法/流暢さ) を意識した模範解答付き`;

  const user = `${exam.name} の ${section.name} セクションの問題を ${qCount} 問生成してください。
トピック: ${topic}
ターゲット: 日本人受験者
出力は以下のJSON形式のみ (他の文字を含めない):
{
  "passage": "(Reading の場合は本文、それ以外は空文字)",
  "audio_script": "(Listening の場合はスクリプト、それ以外は空文字)",
  "prompt": "(Speaking/Writing の場合の出題、それ以外は空文字)",
  "questions": [
    {
      "id": "q1",
      "type": "multiple_choice|short_answer|essay|speaking",
      "stem": "問題文",
      "choices": ["A", "B", "C", "D"],
      "answer": "正解(選択肢index 0始まり、または模範解答テキスト)",
      "explanation": "解説 (日本語)"
    }
  ]
}
Speaking/Writing の場合は choices を空配列、answer に模範解答テキスト、type は "essay" または "speaking" にしてください。`;

  try {
    let payload;
    if (isLiveMode()) {
      payload = await callClaudeJson({ system, user, model: MODEL_DEFAULT, maxTokens: 4000 });
    } else {
      payload = demoQuestions(exam, section, qCount, topic);
    }
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
        <p>${escapeHtml(e.message || String(e))}</p>
        ${isLiveMode() ? '' : '<p style="color:#666;">右上の APIキー欄に Claude API キーを設定すると本番モードで動作します。</p>'}
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
  const section = exam.sections.find(s => s.key === state.sectionKey);
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
    strengths: ['デモモード: APIキー設定で本格採点可能'],
    weaknesses: ['Claude API キー未設定のため、定型コメントのみ'],
    feedback: [],
    studyPlan: 'API キーを設定すると、Claude AI が回答を細かく分析して具体的な学習プランを提示します。',
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
    const sec = exam.sections.find(s => s.key === state.sectionKey);
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
// デモモード fallback
// ==========================================================================
function demoQuestions(exam, section, qCount, topic) {
  const isReading = section.key.includes('reading') || section.key === 'reading';
  const isListening = section.key.includes('listening') || section.key === 'listening' || section.key.startsWith('l_');
  const isSpeaking = section.key === 'speaking';
  const isWriting = section.key === 'writing';

  const passage = isReading ? `[Demo passage on ${topic}] In recent decades, researchers have observed significant changes in this field. Multiple studies suggest that the underlying mechanisms are far more complex than initially believed. The implications extend across various disciplines, prompting interdisciplinary collaboration to address fundamental questions.` : '';
  const audioScript = isListening ? `[Demo listening] Speaker A: I noticed something interesting about ${topic} in our recent study. Speaker B: Really? What did you find? Speaker A: Well, the data suggests that...` : '';
  const prompt = isSpeaking ? `Talk about a memorable experience related to ${topic}. You have 45 seconds to prepare and 60 seconds to speak.` : isWriting ? `Some people believe ${topic} should be a priority in education. Others disagree. Discuss both views and give your opinion. (250+ words)` : '';

  const questions = [];
  for (let i = 1; i <= qCount; i++) {
    if (isSpeaking || isWriting) {
      questions.push({
        id: `q${i}`,
        type: isSpeaking ? 'speaking' : 'essay',
        stem: prompt || `Q${i}: ${topic} について意見を述べてください`,
        choices: [],
        answer: `[Demo model answer] A well-structured response would address ${topic} with concrete examples and clear reasoning.`,
        explanation: 'デモモード: APIキー設定で本格採点が可能になります。',
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
        explanation: 'デモ問題: 本文の "more complex than initially believed" が根拠。実際の試験ではより難解な選択肢になります。',
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
