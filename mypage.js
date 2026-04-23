// ==========================================================================
// Student Mypage - Gamified Learning Dashboard
// ==========================================================================

const KEYS = {
  STUDENTS: 'ai_juku_students',
  CURRENT: 'ai_juku_current_student',
  STATS: 'ai_juku_stats',
  MYPAGE: 'ai_juku_mypage',
};

// Levels & XP progression
const LEVELS = [
  { lv: 1, name: '新米学習者', xp: 0 },
  { lv: 2, name: '初心者', xp: 100 },
  { lv: 3, name: '習慣ビギナー', xp: 250 },
  { lv: 4, name: '習慣化達人', xp: 500 },
  { lv: 5, name: '学習者', xp: 800 },
  { lv: 6, name: '上級学習者', xp: 1200 },
  { lv: 7, name: '見習い受験生', xp: 1700 },
  { lv: 8, name: '実力受験生', xp: 2300 },
  { lv: 9, name: '猛者', xp: 3000 },
  { lv: 10, name: '合格戦士', xp: 4000 },
  { lv: 11, name: '伝説の受験生', xp: 5500 },
  { lv: 12, name: 'レジェンド', xp: 7500 },
];

function getLevel(xp) {
  let current = LEVELS[0];
  let next = LEVELS[1];
  for (let i = 0; i < LEVELS.length; i++) {
    if (xp >= LEVELS[i].xp) { current = LEVELS[i]; next = LEVELS[i + 1] || current; }
  }
  return { current, next };
}

function getCurrentStudent() {
  const students = JSON.parse(localStorage.getItem(KEYS.STUDENTS) || '[]');
  const currentId = JSON.parse(localStorage.getItem(KEYS.CURRENT) || 'null');
  return students.find(s => s.id === currentId) || students[0] || { name: 'ゲスト', grade: '未設定', goal: '未設定' };
}

// 家族プランで兄弟が同端末を使うとマイページデータが混線していたため、
// 生徒IDでキーをスコープする（旧 KEYS.MYPAGE 単一キーからの移行）。
function mypageKeyForCurrentStudent() {
  const s = getCurrentStudent();
  const sid = s && s.id != null ? String(s.id) : 'guest';
  return `${KEYS.MYPAGE}__${sid}`;
}

// 日付を JST (Asia/Tokyo) 基準の 'YYYY-MM-DD' で返す。UTC の toISOString だと
// 日本の深夜学習が前日扱いになりストリークが誤って切れる問題を防ぐ。
function todayKeyJST() {
  const jst = new Date(Date.now() + 9 * 3600 * 1000);
  return jst.toISOString().slice(0, 10);
}

function getMypageData() {
  const key = mypageKeyForCurrentStudent();
  const saved = JSON.parse(localStorage.getItem(key) || 'null');
  if (saved) return saved;
  // Generate realistic starting data
  const data = {
    xp: 680,
    streak: 7,
    streakHistory: [1, 1, 1, 1, 1, 1, 1], // 7 days
    todayMinutes: 45,
    todayQuestions: 5,
    todayXp: 120,
    todayDoneQuests: 2,
    quests: [
      { id: 1, title: '英単語15分', desc: '英検準1級の単語帳を15分', xp: 30, done: true },
      { id: 2, title: 'AIに1問質問', desc: 'わからない問題をAIチューターに聞く', xp: 20, done: true },
      { id: 3, title: '数学演習30分', desc: '青チャート例題3問', xp: 50, done: false },
      { id: 4, title: '英作文1本', desc: 'AIが添削してくれる', xp: 40, done: false },
      { id: 5, title: '学習日記を書く', desc: '今日の振り返りを3行で', xp: 15, done: false },
    ],
    weeklyMinutes: [60, 45, 80, 30, 90, 75, 45],
    lastLogin: todayKeyJST(),
  };
  localStorage.setItem(key, JSON.stringify(data));
  return data;
}

function saveMypageData(data) {
  localStorage.setItem(mypageKeyForCurrentStudent(), JSON.stringify(data));
}

// ==========================================================================
// Render
// ==========================================================================
function render() {
  const student = getCurrentStudent();
  const data = getMypageData();
  const { current, next } = getLevel(data.xp);
  const xpInLevel = data.xp - current.xp;
  const xpNeeded = next.xp - current.xp;
  const pct = Math.min(100, (xpInLevel / xpNeeded) * 100);

  // Header
  document.getElementById('userName').textContent = `${student.name}さん`;
  document.getElementById('userLevel').textContent = `Lv.${current.lv} ${current.name}`;
  document.getElementById('userAvatar').textContent = guessAvatar(student);

  // Streak
  document.getElementById('streakDays').textContent = data.streak;
  renderStreakBars(data.streakHistory);

  // XP
  document.getElementById('xpCurrent').textContent = xpInLevel;
  document.getElementById('xpNext').textContent = xpNeeded;
  document.getElementById('xpGap').textContent = xpNeeded - xpInLevel;
  document.getElementById('xpBar').style.width = `${pct}%`;

  // Quests
  renderQuests(data.quests);
  const done = data.quests.filter(q => q.done).length;
  document.getElementById('questProgress').textContent = `${done}/${data.quests.length} 完了`;

  // Today stats
  document.getElementById('todayMinutes').textContent = data.todayMinutes;
  document.getElementById('todayQ').textContent = data.todayQuestions;
  document.getElementById('todayDone').textContent = done;
  document.getElementById('todayXp').textContent = data.todayXp;

  // Weekly chart
  renderWeeklyChart(data.weeklyMinutes);

  // Motivation
  rotateMotivation();
}

function guessAvatar(student) {
  const name = student.name || '';
  if (name.includes('花子') || name.includes('美') || name.includes('結') || name.includes('あゆみ')) return '👧';
  if (student.grade?.includes('中学')) return '🧒';
  return '👦';
}

function renderStreakBars(history) {
  const container = document.getElementById('streakChart');
  container.innerHTML = '';
  // Show last 14 days
  const days = history.slice(-14);
  while (days.length < 14) days.unshift(0);
  days.forEach((d, i) => {
    const bar = document.createElement('div');
    bar.className = 'streak-bar' + (d ? '' : ' empty');
    bar.style.height = d ? `${30 + Math.random() * 20}px` : '10px';
    container.appendChild(bar);
  });
}

function renderQuests(quests) {
  const container = document.getElementById('questList');
  container.innerHTML = quests.map(q => `
    <div class="quest ${q.done ? 'done' : ''}" data-id="${q.id}">
      <div class="quest-check">${q.done ? '✓' : ''}</div>
      <div class="quest-body">
        <div class="quest-title">${escapeHtml(q.title)}</div>
        <div class="quest-desc">${escapeHtml(q.desc)}</div>
      </div>
      <div class="quest-xp">+${q.xp} XP</div>
    </div>
  `).join('');

  // Toggle quests
  container.querySelectorAll('.quest').forEach(el => {
    el.addEventListener('click', () => toggleQuest(parseInt(el.dataset.id)));
  });
}

function toggleQuest(id) {
  const data = getMypageData();
  const q = data.quests.find(q => q.id === id);
  if (!q) return;
  q.done = !q.done;
  // Update XP
  if (q.done) {
    data.xp += q.xp;
    data.todayXp += q.xp;
    // Celebrate
    celebrate();
  } else {
    data.xp -= q.xp;
    data.todayXp -= q.xp;
  }
  saveMypageData(data);
  render();
}

function celebrate() {
  const celebration = document.createElement('div');
  celebration.textContent = '✨';
  celebration.style.cssText = `
    position: fixed; top: 50%; left: 50%;
    font-size: 5rem; z-index: 999;
    pointer-events: none;
    animation: pop 0.8s ease-out forwards;
  `;
  document.body.appendChild(celebration);
  setTimeout(() => celebration.remove(), 800);

  if (!document.getElementById('popKeyframes')) {
    const style = document.createElement('style');
    style.id = 'popKeyframes';
    style.textContent = `@keyframes pop {
      0% { transform: translate(-50%, -50%) scale(0); opacity: 0; }
      50% { transform: translate(-50%, -50%) scale(1.5); opacity: 1; }
      100% { transform: translate(-50%, -100%) scale(1); opacity: 0; }
    }`;
    document.head.appendChild(style);
  }
}

let weeklyChart = null;
function renderWeeklyChart(minutes) {
  const ctx = document.getElementById('weeklyChart');
  if (weeklyChart) weeklyChart.destroy();
  Chart.defaults.color = '#9ca3af';

  const labels = ['月', '火', '水', '木', '金', '土', '日'];
  weeklyChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: '学習時間 (分)',
        data: minutes,
        backgroundColor: minutes.map((m, i) => {
          const today = new Date().getDay();
          const dayIdx = today === 0 ? 6 : today - 1;
          return i === dayIdx ? 'rgba(236, 72, 153, 0.8)' : 'rgba(99, 102, 241, 0.5)';
        }),
        borderRadius: 8,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' } } }
    }
  });
}

const MOTIVATIONS = [
  { q: '千里の道も一歩から。今日もあなたは確実に成長しています。', a: 'AIコーチ' },
  { q: '今日の1時間は、未来の1年分の差になります。', a: 'AIコーチ' },
  { q: '昨日の自分と比べて、今日はできなかったことが1つできるようになっていますか？', a: 'AIコーチ' },
  { q: '合格は才能ではなく、習慣です。その習慣を今、作っています。', a: 'AIコーチ' },
  { q: 'AIに質問するのは「逃げ」ではなく「成長の近道」です。', a: 'AIコーチ' },
  { q: 'あなたが今日やらなかったことを、ライバルはやっているかもしれません。', a: 'AIコーチ' },
  { q: '完璧を目指さない。ただ昨日より1%前進することを目指そう。', a: 'AIコーチ' },
];

function rotateMotivation() {
  const m = MOTIVATIONS[Math.floor(Math.random() * MOTIVATIONS.length)];
  document.getElementById('motivationText').textContent = `"${m.q}"`;
  document.querySelector('.motivation-author').textContent = m.a;
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c]));
}

// ==========================================================================
// Activity Tracking (for alert system)
// ==========================================================================
function logActivity(type) {
  const student = getCurrentStudent();
  if (!student.id) return;
  const BACKEND = window.location.hostname === 'localhost' && window.location.port === '8090'
    ? 'http://localhost:8000' : window.location.origin;
  fetch(`${BACKEND}/api/activity/log`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ student_id: student.id, type, timestamp: new Date().toISOString() }),
  }).catch(() => {});
}

document.addEventListener('DOMContentLoaded', () => {
  render();
  logActivity('mypage_view');
});
