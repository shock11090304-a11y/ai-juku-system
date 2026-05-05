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
  // Show last 14 days（古い保存データに streakHistory が無い場合の安全策）
  const days = Array.isArray(history) ? history.slice(-14) : [];
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
  // 古い保存データに weeklyMinutes が無い場合の安全策
  const safeMinutes = Array.isArray(minutes) && minutes.length === 7 ? minutes : [0, 0, 0, 0, 0, 0, 0];
  weeklyChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: '学習時間 (分)',
        data: safeMinutes,
        backgroundColor: safeMinutes.map((m, i) => {
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
  if (s == null) return '';
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

// ==========================================================================
// 7日間トライアル体験導線 (Trial Onboarding)
// Day 1-3 で基本機能をマスター → Day 4-7 は自由活用期間
// ==========================================================================
const TRIAL_KEY = 'ai_juku_trial_onboarding';

const TRIAL_DAYS = [
  {
    day: 1,
    title: '志望校カリキュラム作成 & 初質問',
    sub: 'まずあなた専用のカリキュラムを作り、AIチューターに最初の質問をしてみましょう。所要時間: 約15分',
    tasks: [
      { id: 'd1_curriculum', title: '志望校カリキュラムを自動生成', desc: '志望校・現状を入力 → AIが3フェーズ計画を作成', url: 'index.html#tab-curriculum', action: '作成する' },
      { id: 'd1_diagnosis', title: '学習診断を受ける', desc: '今週の学習状況からAIが弱点を分析', url: 'index.html#tab-diagnostic', action: '診断する' },
      { id: 'd1_first_q', title: 'AIチューターに1問質問する', desc: '今わからない問題を1つだけ聞いてみる', url: 'index.html#tab-tutor', action: '質問する' },
    ]
  },
  {
    day: 2,
    title: 'AI問題で弱点を深掘り',
    sub: 'Day 1 の診断から見えた弱点を、AI生成問題で10問練習します。所要時間: 約30分',
    tasks: [
      { id: 'd2_gen_problems', title: 'AI問題を10問生成する', desc: '弱点単元に絞ったオリジナル問題', url: 'index.html#tab-problems', action: '生成する' },
      { id: 'd2_review', title: '今日の復習を完了する', desc: 'エビングハウス復習で「✓正解/✗不正解」を記録', url: 'mypage.html#lbTodayReview', action: '復習する' },
      { id: 'd2_textbook', title: '自分だけの参考書を作る', desc: '弱点特化の教材をAIが執筆', url: 'textbook-generator.html', action: '作成する' },
    ]
  },
  {
    day: 3,
    title: '保護者レポート & 学習計画展開',
    sub: 'カリキュラムを学習計画に取込み、保護者に届くレポートをプレビューします。所要時間: 約5分',
    tasks: [
      { id: 'd3_studyplan', title: 'カリキュラムを学習計画に取込', desc: '試験日まで全期間のタスクを自動展開', url: 'index.html#tab-studyplan', action: '取込む' },
      { id: 'd3_preview_report', title: '保護者向けレポートをプレビュー', desc: '保護者にメールで届く週次レポートを確認', url: 'index.html#tab-parent', action: 'プレビュー' },
      { id: 'd3_moshi', title: '模試結果をアップロード', desc: '画像から偏差値・弱点を自動抽出', url: 'index.html#tab-moshi', action: 'アップロード' },
    ]
  }
];

function getTrialState() {
  const saved = JSON.parse(localStorage.getItem(TRIAL_KEY) || 'null');
  if (saved) return saved;
  // 初回起動 = 今日がトライアル開始日
  const today = todayKeyJST();
  const fresh = {
    startDate: today,
    completed: {}, // { taskId: timestamp }
    dismissed: false,
  };
  localStorage.setItem(TRIAL_KEY, JSON.stringify(fresh));
  return fresh;
}
function saveTrialState(s) {
  localStorage.setItem(TRIAL_KEY, JSON.stringify(s));
}

function getTrialDayNumber(startDate) {
  const start = new Date(startDate + 'T00:00:00+09:00');
  const now = new Date(new Date().toISOString());
  const diffDays = Math.floor((now - start) / (1000 * 60 * 60 * 24));
  return Math.min(7, Math.max(1, diffDays + 1));
}

function renderTrialOnboarding() {
  const section = document.getElementById('trialOnboarding');
  if (!section) return;
  const state = getTrialState();
  // ユーザーが「体験モード終了」を押した、またはトライアル期間(7日)を超えたら非表示
  const todayDayNum = getTrialDayNumber(state.startDate);
  const allTasks = TRIAL_DAYS.flatMap(d => d.tasks);
  const doneTaskCount = allTasks.filter(t => state.completed[t.id]).length;
  const allCompleted = doneTaskCount >= allTasks.length;
  const dayOverflow = todayDayNum > 7;

  if (state.dismissed || (dayOverflow && allCompleted)) {
    section.style.display = 'none';
    return;
  }
  // 期間超過かつ未完了の場合も表示するが終了予告を出す
  section.style.display = 'block';

  // viewingDay が指定されていればそれを優先 (ユーザーが pill をクリックして任意の日を見ている)
  const viewingDayNum = state.viewingDay || todayDayNum;
  const currentDay = TRIAL_DAYS.find(d => d.day === viewingDayNum) || TRIAL_DAYS[2];
  const isPreview = state.viewingDay && state.viewingDay !== todayDayNum;
  document.getElementById('toDayLabel').textContent = `Day ${currentDay.day}`;
  document.getElementById('toDayTitle').textContent = currentDay.title + (isPreview ? '（プレビュー）' : '');
  document.getElementById('toDaySub').textContent = currentDay.sub;
  document.getElementById('toProgressCurrent').textContent = doneTaskCount;
  document.getElementById('toProgressTotal').textContent = allTasks.length;

  // Day pills (クリックで切替可能)
  section.querySelectorAll('.to-day-pill').forEach(pill => {
    const d = parseInt(pill.dataset.day, 10);
    const dayDef = TRIAL_DAYS.find(x => x.day === d);
    const dayTasks = dayDef ? dayDef.tasks : [];
    const dayDone = dayTasks.every(t => state.completed[t.id]);
    pill.classList.remove('active', 'completed');
    if (dayDone) pill.classList.add('completed');
    if (d === currentDay.day) pill.classList.add('active');
    const check = pill.querySelector('.to-day-pill-check');
    if (check) check.textContent = dayDone ? '✓' : (d === currentDay.day ? '…' : '○');
    pill.style.cursor = 'pointer';
    pill.title = `Day ${d} のタスクを表示`;
    // 既存リスナーを置き換える (再描画毎に bind しても重複しないよう onclick 直接代入)
    pill.onclick = () => {
      const s = getTrialState();
      s.viewingDay = d;
      saveTrialState(s);
      renderTrialOnboarding();
    };
  });

  // Tasks for current day
  const tasksEl = document.getElementById('toTasks');
  tasksEl.innerHTML = currentDay.tasks.map(t => {
    const done = !!state.completed[t.id];
    return `
      <div class="to-task ${done ? 'done' : ''}" data-task-id="${t.id}">
        <div class="to-task-check">${done ? '✓' : ''}</div>
        <div class="to-task-body">
          <div class="to-task-title">${escapeHtml(t.title)}</div>
          <div class="to-task-desc">${escapeHtml(t.desc)}</div>
        </div>
        ${done
          ? `<button class="to-task-action to-task-undo" data-task-id="${t.id}" title="完了を取り消す">✓ 完了 <small style="opacity:0.6;">(取消)</small></button>`
          : `<a href="${escapeHtml(t.url)}" class="to-task-action" data-task-id="${t.id}">${escapeHtml(t.action)} →</a>`}
      </div>
    `;
  }).join('');

  // クリックしたらそのタスクを完了にマーク（ユーザーがリンク先で実行したと仮定）
  tasksEl.querySelectorAll('.to-task-action[href]').forEach(a => {
    a.addEventListener('click', (e) => {
      const taskId = a.dataset.taskId;
      state.completed[taskId] = Date.now();
      saveTrialState(state);
      // リンク先で実行中にタブが残るので、戻ってきたとき反映
      setTimeout(renderTrialOnboarding, 100);
    });
  });

  // 「✓ 完了」ボタン → クリックで完了取消(誤タップ救済)
  tasksEl.querySelectorAll('.to-task-undo').forEach(btn => {
    btn.addEventListener('click', () => {
      const taskId = btn.dataset.taskId;
      if (confirm('このタスクの完了を取り消しますか？')) {
        delete state.completed[taskId];
        saveTrialState(state);
        renderTrialOnboarding();
      }
    });
  });

  // 残り時間表示
  const startMs = new Date(state.startDate + 'T00:00:00+09:00').getTime();
  const endMs = startMs + 3 * 24 * 60 * 60 * 1000;
  const leftMs = endMs - Date.now();
  const timeLeft = document.getElementById('toTimeLeft');
  if (leftMs > 0) {
    const hrs = Math.floor(leftMs / (1000 * 60 * 60));
    const d = Math.floor(hrs / 24), h = hrs % 24;
    timeLeft.innerHTML = `⏳ トライアル残り <strong>${d}日 ${h}時間</strong>`;
  } else {
    timeLeft.innerHTML = `⏰ <strong>トライアル期間終了</strong> — 体験を継続するにはプランへアップグレード`;
  }
}

function bindTrialOnboarding() {
  const dismissBtn = document.getElementById('toDismissBtn');
  if (dismissBtn) {
    dismissBtn.addEventListener('click', () => {
      if (!confirm('体験モードを終了しますか？（再表示はできません）')) return;
      const s = getTrialState();
      s.dismissed = true;
      saveTrialState(s);
      renderTrialOnboarding();
    });
  }
}

document.addEventListener('DOMContentLoaded', () => {
  // 各初期化を独立に try/catch して、1つの失敗で以降の初期化が連鎖停止しないようにする
  try { render(); } catch (e) { console.error('render failed:', e); }
  try { logActivity('mypage_view'); } catch (e) { console.error('logActivity failed:', e); }
  try { bindTrialOnboarding(); } catch (e) { console.error('bindTrialOnboarding failed:', e); }
  try { renderTrialOnboarding(); } catch (e) { console.error('renderTrialOnboarding failed:', e); }
  try { initStudyLog(); } catch (e) { console.error('initStudyLog failed:', e); }
  try { initStudyPlan(); } catch (e) { console.error('initStudyPlan failed:', e); }
  try { initMessages(); } catch (e) { console.error('initMessages failed:', e); }
  try { initReferralSection(); } catch (e) { console.error('initReferralSection failed:', e); }
});

// ==========================================================================
// 🎁 紹介ループ UI
// ==========================================================================
async function initReferralSection() {
  const linkInput = document.getElementById('referralLinkInput');
  const copyBtn = document.getElementById('copyReferralBtn');
  const invitedEl = document.getElementById('referralInvited');
  const paidEl = document.getElementById('referralPaid');
  const rewardEl = document.getElementById('referralReward');
  if (!linkInput) return;

  const apiBase = window.location.hostname === 'localhost' && window.location.port === '8090'
    ? 'http://localhost:8000' : window.location.origin;
  const token = (window.AuthGuard && window.AuthGuard.getToken()) || localStorage.getItem('ai_juku_session_token');
  if (!token) { linkInput.value = 'ログイン後に表示されます'; return; }

  try {
    const res = await fetch(`${apiBase}/api/referral/my-link`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) {
      linkInput.value = '取得に失敗しました';
      return;
    }
    const data = await res.json();
    linkInput.value = data.link || '';
    if (invitedEl) invitedEl.textContent = data.invited || 0;
    if (paidEl) paidEl.textContent = data.paid || 0;
    if (rewardEl) rewardEl.textContent = '¥' + (data.reward_yen || 0).toLocaleString();
  } catch (e) {
    console.error('referral fetch failed:', e);
    linkInput.value = '取得エラー';
  }

  if (copyBtn) {
    copyBtn.addEventListener('click', async () => {
      const url = linkInput.value;
      if (!url || url.startsWith('取得') || url.startsWith('ログイン')) return;
      try {
        await navigator.clipboard.writeText(url);
        const orig = copyBtn.textContent;
        copyBtn.textContent = '✅ コピー完了';
        copyBtn.style.background = 'linear-gradient(135deg, #22c55e, #16a34a)';
        setTimeout(() => {
          copyBtn.textContent = orig;
          copyBtn.style.background = 'linear-gradient(135deg, #6366f1, #8b5cf6)';
        }, 2000);
      } catch (e) {
        linkInput.select();
        document.execCommand('copy');
      }
    });
  }

  // 🚀 SNS シェアボタン (review 指摘の友達紹介シェア摩擦を下げる)
  // user の plan により share text を出し分ける
  const student = (window.AuthGuard && window.AuthGuard.getStudent && window.AuthGuard.getStudent()) || null;
  const isStudentAddon = student && student.plan === 'student_addon';

  function _shareText() {
    const url = linkInput.value;
    if (!url || url.startsWith('取得') || url.startsWith('ログイン')) return null;
    if (isStudentAddon) {
      return {
        url,
        text: '塾の友達に教えたい📣 AI学習コーチ塾 — 入塾金¥10,000免除キャンペーン中！\n24時間 AI 質問対応・東大/京大レベルの問題AI自動生成。\n紹介で僕も¥3,000 OFF (Stripe 自動適用)',
      };
    }
    return {
      url,
      text: 'AI学習コーチ塾 — 友達紹介で入塾金¥10,000免除！\n24時間 AI 質問対応・個別カリキュラム自動設計。\n\n👇 紹介URLから登録するとお得',
    };
  }
  const wireShare = (id, builder) => {
    const btn = document.getElementById(id);
    if (!btn) return;
    btn.addEventListener('click', () => {
      const s = _shareText();
      if (!s) return;
      const target = builder(s);
      if (target) window.open(target, '_blank', 'noopener');
    });
  };
  wireShare('shareLineBtn', s => `https://line.me/R/msg/text/?${encodeURIComponent(s.text + '\n' + s.url)}`);
  wireShare('shareThreadsBtn', s => `https://www.threads.net/intent/post?text=${encodeURIComponent(s.text + '\n' + s.url)}`);
  wireShare('shareXBtn', s => `https://twitter.com/intent/tweet?text=${encodeURIComponent(s.text)}&url=${encodeURIComponent(s.url)}`);
  wireShare('shareEmailBtn', s => `mailto:?subject=${encodeURIComponent('AI学習コーチ塾 紹介URL')}&body=${encodeURIComponent(s.text + '\n\n' + s.url)}`);

  // 既存リアル塾生 (student_addon プラン) には専用の audience copy
  // FIX (review): localStorage key 修正 — 'ai_juku_user' は存在しない、AuthGuard.getStudent() を使用
  try {
    const copyEl = document.getElementById('referralAudienceCopy');
    if (copyEl && isStudentAddon) {
      copyEl.innerHTML = '🏫 <strong>リアル塾の友達・クラスメイト</strong>に紹介すれば、あなたは <strong style="color:#a78bfa;">¥3,000 OFF</strong>、相手は <strong style="color:#ec4899;">入塾金 ¥10,000 免除</strong>。塾生プラン限定 永年¥9,800 で広めましょう。';
    }
  } catch (e) { /* noop */ }
}

// ==========================================================================
// 📚 学習記録 (Studyplus 代替・Phase 1)
// 国公立難関大学コース受講生のみ表示。他コースの場合は section 自動非表示。
// ==========================================================================
const SL_API_BASE = window.location.hostname === 'localhost' && window.location.port === '8090'
  ? 'http://localhost:8000' : window.location.origin;

let _slDailyChart = null;

// JST (Asia/Tokyo) 基準で YYYY-MM-DD を返す。Intl 経由でブラウザのローカル TZ に依存しない。
function _slJstDate(offsetDays = 0) {
  const d = new Date(Date.now() - offsetDays * 86400000);
  return new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Tokyo' }).format(d);
}

function _slToken() {
  return (window.AuthGuard && window.AuthGuard.getToken()) || localStorage.getItem('ai_juku_session_token');
}

async function slApiFetch(path, options = {}) {
  const token = _slToken();
  const headers = Object.assign({'Content-Type': 'application/json'}, options.headers || {});
  if (token) headers['Authorization'] = 'Bearer ' + token;
  const res = await fetch(SL_API_BASE + path, Object.assign({}, options, { headers }));
  if (!res.ok) {
    let detail = '';
    try { const j = await res.json(); detail = j.detail || ''; } catch {}
    if (res.status === 401 && window.AuthGuard) {
      // session expired
      try { window.AuthGuard.clearSession && window.AuthGuard.clearSession(); } catch {}
    }
    const err = new Error(detail || `HTTP ${res.status}`);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

function initStudyLog() {
  // 国公立難関大学コース受講生のみ section を表示。
  // auth-guard の /api/auth/me 非同期更新を待つため最大2秒 polling (200ms × 10)
  const section = document.querySelector('.study-log-section');
  const tryInit = (retries) => {
    const student = (window.AuthGuard && window.AuthGuard.getStudent && window.AuthGuard.getStudent()) || null;
    if (!student) {
      if (section) section.style.display = 'none';
      if (retries > 0) setTimeout(() => tryInit(retries - 1), 200);
      return;
    }
    // course フィールドが未取得 (auth refresh 待ち) の場合は polling 継続
    if (typeof student.course === 'undefined' && retries > 0) {
      setTimeout(() => tryInit(retries - 1), 200);
      return;
    }
    const isTarget = student.course === 'kokuritsu_nankan';
    if (!isTarget) {
      // 一般生徒には機能の存在告知 + 申込導線 (機会損失防止)
      if (section) {
        section.style.display = '';
        section.innerHTML = `
          <div class="section-title"><h2>📚 学習記録 <span style="font-size:0.65em;background:linear-gradient(135deg,#fbbf24,#ec4899);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-weight:800;">国公立難関大学コース 限定</span></h2></div>
          <div style="padding:1.2rem; background:rgba(251,191,36,0.06); border:1px dashed rgba(251,191,36,0.35); border-radius:12px; text-align:center;">
            <div style="font-size:2.5rem; margin-bottom:0.5rem;">🎯</div>
            <div style="color:#fbbf24; font-weight:700; font-size:1.05rem; margin-bottom:0.5rem;">国公立難関大学コース 受講生 限定機能</div>
            <p style="color:#a1a1aa; font-size:0.88rem; margin:0.5rem 0 1rem 0;">毎日の学習時間・教材・科目を記録し、塾長から励ましコメント。東大・京大・国公立医学部志望者向けの徹底学習管理を提供します。</p>
            <button type="button" class="course-inquiry-btn" data-course="kokuritsu_nankan" data-source="study-log" style="display:inline-block; padding:0.85rem 1.5rem; background:linear-gradient(135deg,#fbbf24,#ec4899); color:#fff; border:0; border-radius:10px; font-weight:700; font-size:0.95rem; cursor:pointer; box-shadow:0 4px 12px rgba(236,72,153,0.3);">📩 塾長に申込問い合わせをする</button>
            <div class="course-inquiry-msg" style="margin-top:0.7rem; font-size:0.82rem;"></div>
          </div>`;
        bindCourseInquiryButtons(section);
      }
      return;
    }
    if (section) section.style.display = '';
    const dateInput = document.getElementById('slDate');
    if (dateInput) dateInput.value = _slJstDate(0);
    const btn = document.getElementById('slSubmitBtn');
    if (btn && !btn._slBound) {
      btn.addEventListener('click', submitStudyLog);
      btn._slBound = true;
    }
    // 📷 教材写真 AI読取
    const photoBtn = document.getElementById('slMaterialPhotoBtn');
    const photoInput = document.getElementById('slMaterialPhotoInput');
    if (photoBtn && !photoBtn._slBound) {
      photoBtn.addEventListener('click', () => photoInput && photoInput.click());
      photoBtn._slBound = true;
    }
    if (photoInput && !photoInput._slBound) {
      photoInput.addEventListener('change', handleMaterialPhoto);
      photoInput._slBound = true;
    }
    loadMyStudyLogs();
  };
  tryInit(10);
}

// 教材写真を圧縮 → Claude Vision で教材名/科目を抽出して form に auto-fill
async function handleMaterialPhoto(e) {
  const file = e.target.files && e.target.files[0];
  if (!file) return;
  const photoBtn = document.getElementById('slMaterialPhotoBtn');
  const msg = document.getElementById('slMaterialPhotoMsg');
  const matInput = document.getElementById('slMaterial');
  const subjSel = document.getElementById('slSubject');
  if (msg) { msg.style.color = '#a78bfa'; msg.textContent = '🔍 AI が読み取り中... (5-15秒)'; }
  if (photoBtn) { photoBtn.disabled = true; photoBtn.textContent = '⏳'; }
  try {
    // 圧縮 (max 1024px, JPEG q0.8)
    const dataUrl = await _compressImage(file, 1024, 0.8);
    const base64 = dataUrl.split(',')[1];
    const mime = dataUrl.match(/data:(image\/[^;]+);/)[1];
    const token = (window.AuthGuard && window.AuthGuard.getToken()) || localStorage.getItem('ai_juku_session_token');
    const student = (window.AuthGuard && window.AuthGuard.getStudent && window.AuthGuard.getStudent()) || {};
    const sid = student.id || 'guest';
    const res = await fetch(SL_API_BASE + '/api/ai/call', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + (token || '') },
      body: JSON.stringify({
        student_id: sid,
        model: 'claude-sonnet-4-6',
        max_tokens: 500,
        system: 'あなたは日本の中高生向け教材を画像から識別する専門家です。必ず純粋な JSON だけ返答します。',
        messages: [{
          role: 'user',
          content: [
            { type: 'text', text: '画像から教材を識別し、以下の JSON で返してください (フェンスや前置きなし):\n{\n  "title": "教材名 (例: ターゲット1900・青チャート数学IA・新数学スタンダード演習)",\n  "subject": "次のいずれか一致: 英語/数学/国語/現代文/古文/漢文/理科/物理/化学/生物/地学/社会/日本史/世界史/地理/倫理/政経/情報/小論文/面接対策/その他",\n  "confidence": "high|mid|low"\n}\n判別不能なら title:"" にしてください。' },
            { type: 'image', source: { type: 'base64', media_type: mime, data: base64 } }
          ]
        }],
      }),
    });
    if (!res.ok) {
      const errTxt = await res.text();
      throw new Error(`HTTP ${res.status}: ${errTxt.slice(0, 100)}`);
    }
    const data = await res.json();
    const txt = (data.content || []).map(c => c.text || '').join('').trim();
    const jsonStr = txt.replace(/^```(?:json)?\s*|\s*```$/g, '');
    let parsed;
    try { parsed = JSON.parse(jsonStr); }
    catch { const m = jsonStr.match(/\{[\s\S]*\}/); if (m) parsed = JSON.parse(m[0]); else throw new Error('JSON 解析失敗'); }
    if (!parsed.title) {
      if (msg) { msg.style.color = '#fca5a5'; msg.textContent = '❌ 教材を識別できませんでした。手動で入力してください。'; }
      return;
    }
    if (matInput) matInput.value = parsed.title;
    let subjMsg = '';
    if (parsed.subject && subjSel) {
      const opts = Array.from(subjSel.options).map(o => o.value);
      if (opts.includes(parsed.subject)) {
        subjSel.value = parsed.subject;
        subjMsg = ` / 科目: ${parsed.subject}`;
      }
    }
    const conf = parsed.confidence || 'mid';
    const confLabel = { high: '✅ 高精度', mid: '👍 確からしい', low: '⚠️ 低精度・確認推奨' }[conf] || '';
    if (msg) { msg.style.color = '#86efac'; msg.textContent = `${confLabel} 教材名: ${parsed.title}${subjMsg}`; }
  } catch (err) {
    console.error('material photo failed:', err);
    if (msg) { msg.style.color = '#fca5a5'; msg.textContent = '❌ ' + (err.message || '読取失敗'); }
  } finally {
    if (photoBtn) { photoBtn.disabled = false; photoBtn.textContent = '📷'; }
    if (e.target) e.target.value = '';  // 同じファイル再選択を許可
  }
}

// canvas で画像をリサイズ + JPEG 圧縮 (Resend / Anthropic 経由のペイロード上限対策)
function _compressImage(file, maxSide, quality) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error('画像読込失敗'));
    reader.onload = () => {
      const img = new Image();
      img.onerror = () => reject(new Error('画像復号失敗'));
      img.onload = () => {
        const ratio = Math.min(1, maxSide / Math.max(img.width, img.height));
        const w = Math.round(img.width * ratio);
        const h = Math.round(img.height * ratio);
        const canvas = document.createElement('canvas');
        canvas.width = w; canvas.height = h;
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = '#fff';
        ctx.fillRect(0, 0, w, h);
        ctx.drawImage(img, 0, 0, w, h);
        resolve(canvas.toDataURL('image/jpeg', quality));
      };
      img.src = reader.result;
    };
    reader.readAsDataURL(file);
  });
}

async function submitStudyLog() {
  const msg = document.getElementById('slMessage');
  const btn = document.getElementById('slSubmitBtn');
  if (!btn || btn.disabled) return;  // 二重送信防止
  if (msg) { msg.textContent = ''; msg.style.color = '#a1a1aa'; }

  const date = document.getElementById('slDate').value;
  const subject = document.getElementById('slSubject').value;
  const material = document.getElementById('slMaterial').value.trim();
  const minutes = parseInt(document.getElementById('slMinutes').value, 10);
  const pagesRaw = document.getElementById('slPages').value;
  const pages = pagesRaw ? parseInt(pagesRaw, 10) : null;
  const note = document.getElementById('slNote').value.trim();

  if (!subject) { if (msg) { msg.textContent = '科目を選択してください'; msg.style.color = '#fca5a5'; } return; }
  if (!minutes || minutes < 1 || minutes > 1440) { if (msg) { msg.textContent = '勉強時間は 1〜1440 分で入力してください'; msg.style.color = '#fca5a5'; } return; }

  btn.disabled = true;
  btn.textContent = '保存中...';
  try {
    await slApiFetch('/api/study-logs', {
      method: 'POST',
      body: JSON.stringify({
        studied_date: date || undefined,
        subject, material: material || undefined,
        minutes, pages, note: note || undefined,
      }),
    });
    if (msg) { msg.textContent = '✅ 記録しました！'; msg.style.color = '#86efac'; }
    document.getElementById('slMaterial').value = '';
    document.getElementById('slMinutes').value = '';
    document.getElementById('slPages').value = '';
    document.getElementById('slNote').value = '';
    await loadMyStudyLogs();
  } catch (e) {
    if (msg) { msg.textContent = '❌ ' + (e.message || '保存に失敗しました'); msg.style.color = '#fca5a5'; }
  } finally {
    btn.disabled = false;
    btn.textContent = '📝 記録を保存';
  }
}

async function loadMyStudyLogs() {
  const list = document.getElementById('slLogList');
  const summary = document.getElementById('slSummary');
  try {
    const data = await slApiFetch('/api/study-logs/me?days=30&limit=200');
    const logs = data.logs || [];
    const daily = data.daily || [];
    const totEl = document.getElementById('slTotalMin');
    const daEl = document.getElementById('slDaysActive');
    const lcEl = document.getElementById('slLogCount');
    if (totEl) totEl.textContent = (data.total_minutes || 0).toLocaleString();
    if (daEl) daEl.textContent = (data.days_active || 0);
    if (lcEl) lcEl.textContent = logs.length;
    // empty state: サマリーカードを「最初の1件を記録しよう」hint に置換
    if (summary) {
      if (logs.length === 0) {
        summary.style.gridTemplateColumns = '1fr';
        summary.innerHTML = `<div style="background:rgba(251,191,36,0.08); border:1px dashed rgba(251,191,36,0.3); border-radius:10px; padding:1rem; text-align:center;"><div style="color:#fbbf24; font-weight:700; font-size:0.95rem;">📝 まずは1件記録してみよう！</div><div style="font-size:0.78rem; color:#a1a1aa; margin-top:0.3rem;">毎日の積み重ねが志望校合格への最短ルート</div></div>`;
      } else {
        // re-render normal summary if previously empty
        if (!totEl) {
          summary.style.gridTemplateColumns = 'repeat(auto-fit, minmax(110px, 1fr))';
          summary.innerHTML = `
            <div style="background:rgba(99,102,241,0.1); border-radius:10px; padding:0.85rem; text-align:center;"><div style="font-size:0.72rem; color:#a1a1aa;">直近30日 合計</div><div style="font-size:1.4rem; font-weight:800; color:#c7d2fe;"><span id="slTotalMin">${(data.total_minutes || 0).toLocaleString()}</span>分</div></div>
            <div style="background:rgba(99,102,241,0.1); border-radius:10px; padding:0.85rem; text-align:center;"><div style="font-size:0.72rem; color:#a1a1aa;">学習日数</div><div style="font-size:1.4rem; font-weight:800; color:#c7d2fe;"><span id="slDaysActive">${data.days_active || 0}</span>日</div></div>
            <div style="background:rgba(99,102,241,0.1); border-radius:10px; padding:0.85rem; text-align:center;"><div style="font-size:0.72rem; color:#a1a1aa;">記録回数</div><div style="font-size:1.4rem; font-weight:800; color:#c7d2fe;"><span id="slLogCount">${logs.length}</span>回</div></div>`;
        }
      }
    }
    renderSlDailyChart(daily);
    renderSlLogList(logs);
  } catch (e) {
    console.error('loadMyStudyLogs failed:', e);
    if (list) {
      list.innerHTML = `<div style="text-align:center; color:#fca5a5; padding:1rem;">⚠️ 記録の読み込みに失敗しました (${escapeHtml(e.message || '')}) <button id="slRetryBtn" style="margin-left:0.5rem; background:rgba(99,102,241,0.2); border:0; color:#c7d2fe; padding:0.3rem 0.6rem; border-radius:6px; cursor:pointer;">再試行</button></div>`;
      const retryBtn = document.getElementById('slRetryBtn');
      if (retryBtn) retryBtn.addEventListener('click', loadMyStudyLogs);
    }
  }
}

function renderSlDailyChart(daily) {
  const canvas = document.getElementById('slDailyChart');
  if (!canvas || !window.Chart) {
    if (canvas) canvas.parentElement.innerHTML = '<div style="text-align:center; color:#71717a; padding:1rem; font-size:0.85rem;">グラフを読み込めません</div>';
    return;
  }
  // JST 30 日分 (Intl 経由で TZ 安全)
  const map = {};
  (daily || []).forEach(d => { if (d && d.date) map[String(d.date).slice(0, 10)] = d.minutes || 0; });
  const labels = [];
  const values = [];
  for (let i = 29; i >= 0; i--) {
    const key = _slJstDate(i);
    labels.push(key.slice(5));
    values.push(map[key] || 0);
  }
  if (_slDailyChart) _slDailyChart.destroy();
  _slDailyChart = new Chart(canvas, {
    type: 'bar',
    data: { labels, datasets: [{ label: '分', data: values, backgroundColor: 'rgba(99,102,241,0.6)', borderColor: 'rgba(99,102,241,1)', borderWidth: 1 }] },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: '#a1a1aa', font: { size: 9 } }, grid: { color: 'rgba(255,255,255,0.05)' } },
        y: { ticks: { color: '#a1a1aa' }, grid: { color: 'rgba(255,255,255,0.05)' }, beginAtZero: true },
      },
    },
  });
}

function renderSlLogList(logs) {
  const list = document.getElementById('slLogList');
  if (!list) return;
  if (!logs.length) {
    list.innerHTML = '<div style="text-align:center; color:#71717a; padding:2rem;">まだ記録がありません。今日勉強した内容を記録してみよう！</div>';
    return;
  }
  list.innerHTML = logs.map(l => {
    const reactions = l.reactions || { likes: 0, comments: [] };
    const commentsHtml = (reactions.comments || []).map(c =>
      `<div style="background:rgba(255,255,255,0.04); padding:0.5rem 0.75rem; border-radius:8px; margin-top:0.4rem; font-size:0.82rem;">
        <span style="color:#fbbf24; font-weight:700;">塾長:</span>
        <span style="color:#e4e4e7;">${escapeHtml(c.comment)}</span>
      </div>`
    ).join('');
    const likeBadge = reactions.likes > 0
      ? `<span style="background:rgba(236,72,153,0.18); color:#f9a8d4; padding:0.15rem 0.5rem; border-radius:999px; font-size:0.72rem; margin-left:0.5rem;" aria-label="いいね ${reactions.likes} 件">❤️ ${reactions.likes}</span>`
      : '';
    const hasAdminComment = (reactions.comments || []).some(c => c.actor_type === 'admin');
    return `
      <div style="background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.06); border-radius:10px; padding:0.85rem; margin-bottom:0.5rem;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.4rem;">
          <div>
            <span style="font-weight:700; color:#c7d2fe;">${escapeHtml(l.subject)}</span>
            ${l.material ? `<span style="color:#a1a1aa; font-size:0.85rem;"> - ${escapeHtml(l.material)}</span>` : ''}
            ${likeBadge}
          </div>
          <div style="font-size:0.75rem; color:#71717a;">
            ${escapeHtml(l.date)} · ${l.minutes}分${l.pages ? ' · ' + l.pages + 'p' : ''}
            ${hasAdminComment ? '' : `<button data-log-id="${l.id}" class="sl-delete-btn" aria-label="この記録を削除" title="削除" style="background:none; border:0; color:#71717a; cursor:pointer; margin-left:0.5rem; font-size:0.9rem;">🗑</button>`}
          </div>
        </div>
        ${l.note ? `<div style="font-size:0.85rem; color:#d4d4d8; margin-top:0.3rem;">${escapeHtml(l.note)}</div>` : ''}
        ${commentsHtml}
      </div>`;
  }).join('');
  list.querySelectorAll('.sl-delete-btn').forEach(b => {
    b.addEventListener('click', async (e) => {
      const id = e.currentTarget.getAttribute('data-log-id');
      if (!confirm('この記録を削除しますか？\n（一度削除すると元に戻せません）')) return;
      try {
        await slApiFetch(`/api/study-logs/${encodeURIComponent(id)}`, { method: 'DELETE' });
        await loadMyStudyLogs();
      } catch (err) {
        alert('削除に失敗しました: ' + (err.message || ''));
      }
    });
  });
}


// ==========================================================================
// 📅 学習計画 (Phase 2 - 国公立難関大学コース受講生限定)
// ==========================================================================
const SP_SUBJECTS = ['英語','数学','国語','現代文','古文','漢文','理科','物理','化学','生物','地学','社会','日本史','世界史','地理','倫理','政経','情報','小論文','面接対策','その他'];
let _spLastPlans = []; // editStudyPlan で再 fetch 不要 (Frontend M-5)

function initStudyPlan() {
  const section = document.querySelector('.study-plan-section');
  const tryInit = (retries) => {
    const student = (window.AuthGuard && window.AuthGuard.getStudent && window.AuthGuard.getStudent()) || null;
    if (!student) {
      if (section) section.style.display = 'none';
      if (retries > 0) setTimeout(() => tryInit(retries - 1), 200);
      return;
    }
    if (typeof student.course === 'undefined' && retries > 0) {
      setTimeout(() => tryInit(retries - 1), 200);
      return;
    }
    if (student.course !== 'kokuritsu_nankan') {
      // 一般生徒には CTA 表示 (Frontend m-1: 機会損失防止)
      if (section) {
        section.style.display = '';
        section.innerHTML = `
          <div class="section-title"><h2>📅 学習計画 <span style="font-size:0.65em;background:linear-gradient(135deg,#fbbf24,#ec4899);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-weight:800;">国公立難関大学コース 限定</span></h2></div>
          <div style="padding:1.2rem; background:rgba(251,191,36,0.06); border:1px dashed rgba(251,191,36,0.35); border-radius:12px; text-align:center;">
            <div style="font-size:2.5rem; margin-bottom:0.5rem;">📅</div>
            <div style="color:#fbbf24; font-weight:700; font-size:1.05rem; margin-bottom:0.5rem;">志望校合格までのロードマップを描こう</div>
            <p style="color:#a1a1aa; font-size:0.88rem; margin:0.5rem 0 1rem 0;">学習計画 + 進捗ガントチャート + 月間カレンダーで「いつまでに何を」を可視化。</p>
            <button type="button" class="course-inquiry-btn" data-course="kokuritsu_nankan" data-source="study-plan" style="display:inline-block; padding:0.85rem 1.5rem; background:linear-gradient(135deg,#fbbf24,#ec4899); color:#fff; border:0; border-radius:10px; font-weight:700; font-size:0.95rem; cursor:pointer; box-shadow:0 4px 12px rgba(236,72,153,0.3);">📩 塾長に申込問い合わせをする</button>
            <div class="course-inquiry-msg" style="margin-top:0.7rem; font-size:0.82rem;"></div>
          </div>`;
        bindCourseInquiryButtons(section);
      }
      return;
    }
    if (section) section.style.display = '';
    // populate subject options
    const subjSel = document.getElementById('spSubject');
    if (subjSel && !subjSel.options.length) {
      SP_SUBJECTS.forEach(s => {
        const o = document.createElement('option');
        o.value = s; o.textContent = s;
        subjSel.appendChild(o);
      });
    }
    // default dates: today / today+30
    const today = _slJstDate(0);
    const future = _slJstDate(-30);  // _slJstDate(offsetDays) は -offsetDays するので future = -30 を渡す
    const sd = document.getElementById('spStart');
    const ed = document.getElementById('spEnd');
    if (sd && !sd.value) sd.value = today;
    if (ed && !ed.value) ed.value = future;
    // bind
    const toggle = document.getElementById('spToggleFormBtn');
    const wrap = document.getElementById('spFormWrap');
    const cancelBtn = document.getElementById('spCancelBtn');
    const saveBtn = document.getElementById('spSaveBtn');
    if (toggle && !toggle._spBound) {
      toggle.addEventListener('click', () => {
        const willOpen = wrap.style.display === 'none';
        wrap.style.display = willOpen ? '' : 'none';
        // 開く時に編集中だったらクリア (Frontend C-2: 別計画として複製作成事故防止)
        if (willOpen && wrap.dataset.editId) clearSpForm();
      });
      toggle._spBound = true;
    }
    if (cancelBtn && !cancelBtn._spBound) {
      cancelBtn.addEventListener('click', () => { wrap.style.display = 'none'; clearSpForm(); });
      cancelBtn._spBound = true;
    }
    if (saveBtn && !saveBtn._spBound) {
      saveBtn.addEventListener('click', submitStudyPlan);
      saveBtn._spBound = true;
    }
    // AI 機能 (A+B+C)
    bindStudyPlanAiButtons();
    loadMyStudyPlans();
  };
  tryInit(10);
}

// ==========================================================================
// 🤖 学習計画 AI 機能 (A: 計画自動生成 / B: 進捗診断 / C: 教材推薦)
// ==========================================================================
function bindStudyPlanAiButtons() {
  const aiGenBtn = document.getElementById('spAiGenBtn');
  const aiRecBtn = document.getElementById('spAiRecBtn');
  const aiGenSubmit = document.getElementById('spAiGenSubmit');
  const aiRecSubmit = document.getElementById('spRecSubmit');
  const recSubj = document.getElementById('spRecSubject');
  if (aiGenBtn && !aiGenBtn._spAiBound) {
    aiGenBtn.addEventListener('click', () => {
      const w = document.getElementById('spAiGenWrap');
      const w2 = document.getElementById('spAiRecWrap');
      const isOpen = w.style.display !== 'none';
      w.style.display = isOpen ? 'none' : '';
      if (!isOpen) {
        w2.style.display = 'none';
        // default values
        const today = _slJstDate(0);
        const future = _slJstDate(-90);  // 90 日後
        if (!document.getElementById('spAiStart').value) document.getElementById('spAiStart').value = today;
        if (!document.getElementById('spAiEnd').value) document.getElementById('spAiEnd').value = future;
        if (!document.getElementById('spAiDailyMin').value) document.getElementById('spAiDailyMin').value = '60';
      }
    });
    aiGenBtn._spAiBound = true;
  }
  if (aiRecBtn && !aiRecBtn._spAiBound) {
    aiRecBtn.addEventListener('click', () => {
      const w = document.getElementById('spAiRecWrap');
      const w2 = document.getElementById('spAiGenWrap');
      const isOpen = w.style.display !== 'none';
      w.style.display = isOpen ? 'none' : '';
      if (!isOpen) {
        w2.style.display = 'none';
        // populate subject options
        if (recSubj && !recSubj.options.length) {
          recSubj.innerHTML = '<option value="">-- 苦手科目を選択 --</option>' + SP_SUBJECTS.map(s => `<option value="${s}">${s}</option>`).join('');
        }
      }
    });
    aiRecBtn._spAiBound = true;
  }
  if (aiGenSubmit && !aiGenSubmit._spAiBound) {
    aiGenSubmit.addEventListener('click', generateStudyPlanWithAi);
    aiGenSubmit._spAiBound = true;
  }
  if (aiRecSubmit && !aiRecSubmit._spAiBound) {
    aiRecSubmit.addEventListener('click', recommendTextbooksWithAi);
    aiRecSubmit._spAiBound = true;
  }
}

async function _spCallAi(systemPrompt, userText, maxTokens) {
  const token = (window.AuthGuard && window.AuthGuard.getToken()) || localStorage.getItem('ai_juku_session_token');
  const student = (window.AuthGuard && window.AuthGuard.getStudent && window.AuthGuard.getStudent()) || {};
  const sid = student.id || 'guest';
  const res = await fetch(SL_API_BASE + '/api/ai/call', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + (token || '') },
    body: JSON.stringify({
      student_id: sid,
      model: 'claude-sonnet-4-6',
      max_tokens: maxTokens || 1500,
      system: systemPrompt,
      messages: [{ role: 'user', content: userText }],
    }),
  });
  if (!res.ok) {
    const errTxt = await res.text();
    throw new Error(`HTTP ${res.status}: ${errTxt.slice(0, 100)}`);
  }
  const data = await res.json();
  const txt = (data.content || []).map(c => c.text || '').join('').trim();
  const jsonStr = txt.replace(/^```(?:json)?\s*|\s*```$/g, '');
  try { return JSON.parse(jsonStr); }
  catch { const m = jsonStr.match(/[\[\{][\s\S]*[\]\}]/); if (m) return JSON.parse(m[0]); throw new Error('JSON 解析失敗'); }
}

// ============ A: AI 計画自動生成 ============
async function generateStudyPlanWithAi() {
  const btn = document.getElementById('spAiGenSubmit');
  const msg = document.getElementById('spAiGenMsg');
  const proposalsEl = document.getElementById('spAiGenProposals');
  if (!btn || btn.disabled) return;
  const goal = document.getElementById('spAiGoal').value.trim();
  const material = document.getElementById('spAiMaterial').value.trim();
  const start = document.getElementById('spAiStart').value;
  const end = document.getElementById('spAiEnd').value;
  const dailyMin = parseInt(document.getElementById('spAiDailyMin').value, 10) || 60;
  if (!goal) { msg.style.color = '#fca5a5'; msg.textContent = '志望校は必須です'; return; }
  if (!start || !end) { msg.style.color = '#fca5a5'; msg.textContent = '期間を入力してください'; return; }
  if (end < start) { msg.style.color = '#fca5a5'; msg.textContent = '終了日は開始日以降にしてください'; return; }

  btn.disabled = true; btn.textContent = '🤖 AI 生成中... (10-30秒)';
  msg.style.color = '#c4b5fd'; msg.textContent = '🤖 受験戦略を考えています...';
  proposalsEl.innerHTML = '';
  try {
    const days = Math.max(1, Math.round((new Date(end) - new Date(start)) / 86400000) + 1);
    const totalMin = days * dailyMin;
    const sysPrompt = '受験戦略を立てる学習プランナーです。指定の志望校に必要な科目構成を考慮し、現実的な学習計画を立てます。教師名や塾名は出さず、純粋な JSON だけ返答します。';
    const userPrompt = `志望校: ${goal}\n${material ? '優先教材: ' + material + '\n' : ''}期間: ${start} 〜 ${end} (${days}日間)\n1日確保時間: ${dailyMin} 分 (期間総計 ${totalMin} 分)\n\n受験戦略上、上記期間に並列で進めるべき計画を 3〜5件 提案してください。各計画は study_plans に登録される単位 (1 教材 or 1 単元 単位)。\n\n出力形式 (フェンスや前置きなし、純粋な JSON):\n[\n  {\n    "title": "タイトル (40文字以内)",\n    "subject": "次から1つ: 英語/数学/国語/現代文/古文/漢文/理科/物理/化学/生物/地学/社会/日本史/世界史/地理/倫理/政経/情報/小論文/面接対策/その他",\n    "material": "推奨教材名 (40文字以内、例: ターゲット1900・青チャート数学IA)",\n    "start_date": "${start}",\n    "end_date": "YYYY-MM-DD (期間内の現実的な終了日)",\n    "target_minutes": 整数 (期間総分数の妥当な配分),\n    "target_pages": 整数 or null,\n    "color": "#RRGGBB (科目別に視認性高く: 英#6366f1 数#10b981 国#ec4899 理#f59e0b 社#8b5cf6 等)",\n    "rationale": "この計画を提案する理由 (60文字以内)"\n  }\n]\n注: target_minutes 合計は期間総計の 80〜100% に収めること。期間が短い (30日以下) なら 3件、長い (180日以上) なら 5件まで。`;
    const proposals = await _spCallAi(sysPrompt, userPrompt, 2500);
    if (!Array.isArray(proposals) || !proposals.length) throw new Error('提案が空でした');

    msg.style.color = '#86efac'; msg.textContent = `✅ ${proposals.length} 件の計画案を生成しました`;
    proposalsEl.innerHTML = `
      <div style="margin-top:0.5rem; padding:0.7rem; background:rgba(0,0,0,0.25); border-radius:8px;">
        ${proposals.map((p, i) => `
          <label style="display:block; padding:0.6rem 0.7rem; background:rgba(255,255,255,0.04); border-left:3px solid ${escapeHtml(p.color || '#6366f1')}; border-radius:6px; margin-bottom:0.4rem; cursor:pointer;">
            <input type="checkbox" data-idx="${i}" class="sp-ai-prop-check" checked style="vertical-align:middle; margin-right:0.4rem;">
            <span style="font-weight:700; color:#e4e4e7;">${escapeHtml(p.title || '')}</span>
            <span style="font-size:0.72rem; color:#a1a1aa; margin-left:0.3rem;">[${escapeHtml(p.subject || '')}]</span>
            <div style="font-size:0.78rem; color:#a1a1aa; margin-top:0.2rem; margin-left:1.5rem;">
              ${escapeHtml(p.start_date || '')} 〜 ${escapeHtml(p.end_date || '')} ・ 目標 ${p.target_minutes || 0}分${p.target_pages ? ' / ' + p.target_pages + 'p' : ''} ・ ${escapeHtml(p.material || '教材未指定')}
            </div>
            ${p.rationale ? `<div style="font-size:0.75rem; color:#c4b5fd; margin-top:0.2rem; margin-left:1.5rem;">💡 ${escapeHtml(p.rationale)}</div>` : ''}
          </label>
        `).join('')}
        <button id="spAiAddSelected" type="button" style="width:100%; margin-top:0.5rem; padding:0.6rem; background:linear-gradient(135deg,#6366f1,#a78bfa); border:0; border-radius:8px; color:#fff; font-weight:700; cursor:pointer;">✨ 選択した計画を追加</button>
        <div id="spAiAddMsg" style="margin-top:0.4rem; font-size:0.78rem; min-height:1em;"></div>
      </div>`;
    document.getElementById('spAiAddSelected').addEventListener('click', () => addAiProposalsToPlans(proposals));
  } catch (e) {
    msg.style.color = '#fca5a5'; msg.textContent = '❌ ' + (e.message || '生成失敗');
  } finally {
    btn.disabled = false; btn.textContent = '✨ 計画を生成する';
  }
}

async function addAiProposalsToPlans(proposals) {
  const checks = Array.from(document.querySelectorAll('.sp-ai-prop-check:checked'));
  const addMsg = document.getElementById('spAiAddMsg');
  if (!checks.length) { addMsg.style.color = '#fca5a5'; addMsg.textContent = '少なくとも 1 件選択してください'; return; }
  const btn = document.getElementById('spAiAddSelected');
  btn.disabled = true;
  let ok = 0, fail = 0;
  for (const ck of checks) {
    const i = parseInt(ck.getAttribute('data-idx'), 10);
    const p = proposals[i];
    if (!p) { fail++; continue; }
    try {
      await slApiFetch('/api/study-plans', {
        method: 'POST',
        body: JSON.stringify({
          title: p.title, subject: p.subject, material: p.material || undefined,
          start_date: p.start_date, end_date: p.end_date,
          target_minutes: p.target_minutes || undefined, target_pages: p.target_pages || undefined,
          color: p.color || undefined, note: p.rationale || undefined,
        }),
      });
      ok++;
    } catch { fail++; }
  }
  addMsg.style.color = ok ? '#86efac' : '#fca5a5';
  addMsg.textContent = `✅ ${ok} 件追加${fail ? ` / ❌ ${fail} 件失敗` : ''}`;
  if (ok > 0) {
    document.getElementById('spAiGenWrap').style.display = 'none';
    await loadMyStudyPlans();
  }
  btn.disabled = false;
}

// ============ B: AI 進捗診断 ============
async function diagStudyPlanWithAi(planId) {
  const plan = (_spLastPlans || []).find(p => String(p.id) === String(planId));
  if (!plan) { alert('計画が見つかりません'); return; }
  // modal を作る (simple)
  let modal = document.getElementById('spDiagModal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'spDiagModal';
    modal.style.cssText = 'position:fixed; inset:0; background:rgba(0,0,0,0.7); z-index:9999; display:flex; align-items:flex-start; justify-content:center; padding:2rem; overflow-y:auto;';
    modal.innerHTML = `
      <div style="background:#0f172a; border:1px solid rgba(167,139,250,0.4); border-radius:14px; padding:1.5rem; max-width:600px; width:100%;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
          <h3 style="margin:0; color:#c4b5fd;">🤖 AI 進捗診断</h3>
          <button id="spDiagClose" type="button" style="background:none; border:0; color:#a1a1aa; font-size:1.5rem; cursor:pointer;">×</button>
        </div>
        <div id="spDiagBody"></div>
      </div>`;
    document.body.appendChild(modal);
    modal.querySelector('#spDiagClose').addEventListener('click', () => modal.style.display = 'none');
    modal.addEventListener('click', e => { if (e.target === modal) modal.style.display = 'none'; });
  }
  modal.style.display = 'flex';
  const body = modal.querySelector('#spDiagBody');
  body.innerHTML = '<div style="text-align:center; padding:2rem; color:#a1a1aa;">🤖 診断中... (5-15秒)</div>';

  try {
    const today = _slJstDate(0);
    const totalDays = Math.max(1, Math.round((new Date(plan.end_date) - new Date(plan.start_date)) / 86400000) + 1);
    const elapsedDays = Math.max(0, Math.min(totalDays, Math.round((new Date(today) - new Date(plan.start_date)) / 86400000) + 1));
    const remainDays = Math.max(0, Math.round((new Date(plan.end_date) - new Date(today)) / 86400000));
    const sysPrompt = '学習進捗を客観的に診断するコーチです。データから現実的な評価と次の一手を 200 字程度で示します。教師名は出さず、純粋な JSON のみ返答します。';
    const userPrompt = `計画タイトル: ${plan.title}\n科目: ${plan.subject}\n教材: ${plan.material || '未指定'}\n期間: ${plan.start_date} 〜 ${plan.end_date} (全 ${totalDays}日 / 経過 ${elapsedDays}日 / 残 ${remainDays}日)\n目標: ${plan.target_minutes || '未設定'}分${plan.target_pages ? ' / ' + plan.target_pages + 'p' : ''}\n実績: ${plan.actual_minutes}分${plan.actual_pages ? ' / ' + plan.actual_pages + 'p' : ''}\n進捗率: ${plan.progress_minutes_pct ?? '—'}% (時間) ${plan.progress_pages_pct ? '/ ' + plan.progress_pages_pct + '% (ページ)' : ''}\n\n上記から JSON で診断結果を返してください (フェンスや前置きなし):\n{\n  "verdict": "great|good|warning|critical",\n  "verdict_label": "評価ラベル (例: 順調 / 要注意 / 危機的)",\n  "elapsed_pct": 整数 (経過率%),\n  "summary": "現状サマリ (60字)",\n  "actions": ["次の一手 1 (40字)", "次の一手 2 (40字)", "次の一手 3 (40字)"]\n}`;
    const result = await _spCallAi(sysPrompt, userPrompt, 800);
    const verdictColor = { great: '#34d399', good: '#86efac', warning: '#fbbf24', critical: '#fca5a5' }[result.verdict] || '#a78bfa';
    const verdictIcon = { great: '🎉', good: '✅', warning: '⚠️', critical: '🚨' }[result.verdict] || '🤖';
    body.innerHTML = `
      <div style="background:rgba(255,255,255,0.04); border-left:4px solid ${verdictColor}; border-radius:8px; padding:0.9rem; margin-bottom:0.8rem;">
        <div style="font-size:1.1rem; color:${verdictColor}; font-weight:800; margin-bottom:0.4rem;">${verdictIcon} ${escapeHtml(result.verdict_label || '')} <span style="font-size:0.8rem; color:#a1a1aa;">(経過 ${result.elapsed_pct ?? '—'}%)</span></div>
        <div style="color:#e4e4e7; font-size:0.92rem;">${escapeHtml(result.summary || '')}</div>
      </div>
      <div style="font-weight:700; color:#c4b5fd; font-size:0.88rem; margin-bottom:0.4rem;">📋 次の一手</div>
      ${(result.actions || []).map(a => `<div style="background:rgba(255,255,255,0.04); border-radius:6px; padding:0.55rem 0.7rem; margin-bottom:0.35rem; font-size:0.88rem; color:#e4e4e7;">→ ${escapeHtml(a)}</div>`).join('')}
      <div style="font-size:0.7rem; color:#71717a; margin-top:0.7rem; text-align:right;">AI による参考診断です。最終判断は塾長と相談してください。</div>`;
  } catch (e) {
    body.innerHTML = `<div style="color:#fca5a5; padding:1rem;">❌ 診断失敗: ${escapeHtml(e.message || '')}</div>`;
  }
}

// ============ C: AI 教材推薦 ============
async function recommendTextbooksWithAi() {
  const btn = document.getElementById('spRecSubmit');
  const msg = document.getElementById('spRecMsg');
  const resultsEl = document.getElementById('spRecResults');
  if (!btn || btn.disabled) return;
  const goal = document.getElementById('spRecGoal').value.trim();
  const subj = document.getElementById('spRecSubject').value;
  if (!goal) { msg.style.color = '#fca5a5'; msg.textContent = '志望校は必須です'; return; }
  if (!subj) { msg.style.color = '#fca5a5'; msg.textContent = '苦手科目を選択してください'; return; }

  btn.disabled = true; btn.textContent = '🎯 AI 推薦中...';
  msg.style.color = '#fbbf24'; msg.textContent = '🎯 教材を選定しています...';
  resultsEl.innerHTML = '';
  try {
    const sysPrompt = '受験参考書アドバイザーです。志望校レベルと苦手科目に応じて段階的に取り組むべき定番教材を推薦します。教師名は出さず、JSON のみ返答します。';
    const userPrompt = `志望校: ${goal}\n苦手科目: ${subj}\n\n上記の生徒に適した教材を 3〜5 件、易→難の順で推薦してください。出力 (フェンスや前置きなし):\n[\n  {"title": "教材名 (例: 大岩のいちばんはじめの英文法)", "level": "基礎/標準/応用/発展", "reason": "推薦理由 (50字)", "estimated_days": 整数 (推奨完走日数), "estimated_minutes_total": 整数 (期間総分数の目安)}\n]`;
    const recs = await _spCallAi(sysPrompt, userPrompt, 1500);
    if (!Array.isArray(recs) || !recs.length) throw new Error('推薦が空でした');
    msg.style.color = '#86efac'; msg.textContent = `✅ ${recs.length} 件の教材を推薦`;
    resultsEl.innerHTML = recs.map((r, i) => `
      <div style="background:rgba(255,255,255,0.04); border-left:3px solid #fbbf24; border-radius:6px; padding:0.7rem; margin-bottom:0.5rem;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.3rem;">
          <div style="font-weight:700; color:#e4e4e7;">${i + 1}. ${escapeHtml(r.title || '')}</div>
          <span style="font-size:0.72rem; background:rgba(251,191,36,0.2); color:#fbbf24; padding:0.1rem 0.5rem; border-radius:4px;">${escapeHtml(r.level || '')}</span>
        </div>
        <div style="font-size:0.82rem; color:#d4d4d8; margin-bottom:0.4rem;">💡 ${escapeHtml(r.reason || '')}</div>
        <div style="font-size:0.75rem; color:#a1a1aa; margin-bottom:0.4rem;">⏱ 推奨完走 ${r.estimated_days || '—'}日 / 計 ${r.estimated_minutes_total || '—'}分</div>
        <button data-rec-idx="${i}" class="sp-rec-add-btn" type="button" style="background:linear-gradient(135deg,#fbbf24,#10b981); color:#fff; border:0; padding:0.35rem 0.8rem; border-radius:6px; cursor:pointer; font-size:0.78rem; font-weight:700;">📅 この教材で計画を作成</button>
      </div>`).join('');
    resultsEl.querySelectorAll('.sp-rec-add-btn').forEach(b => b.addEventListener('click', () => {
      const i = parseInt(b.getAttribute('data-rec-idx'), 10);
      const r = recs[i];
      // A の form に pre-fill して開く
      document.getElementById('spAiRecWrap').style.display = 'none';
      document.getElementById('spAiGenWrap').style.display = '';
      document.getElementById('spAiGoal').value = goal;
      document.getElementById('spAiMaterial').value = r.title || '';
      document.getElementById('spAiStart').value = _slJstDate(0);
      document.getElementById('spAiEnd').value = _slJstDate(-(r.estimated_days || 30));
      document.getElementById('spAiDailyMin').value = Math.max(15, Math.round((r.estimated_minutes_total || 1800) / (r.estimated_days || 30)));
      // 自動生成も即座にトリガー
      generateStudyPlanWithAi();
    }));
  } catch (e) {
    msg.style.color = '#fca5a5'; msg.textContent = '❌ ' + (e.message || '推薦失敗');
  } finally {
    btn.disabled = false; btn.textContent = '🎯 教材を推薦する';
  }
}

function clearSpForm() {
  const ids = ['spTitle','spMaterial','spTargetMin','spTargetPages','spNote'];
  ids.forEach(id => { const el = document.getElementById(id); if (el) el.value = ''; });
  const wrap = document.getElementById('spFormWrap');
  if (wrap) wrap.dataset.editId = '';
  const saveBtn = document.getElementById('spSaveBtn');
  if (saveBtn) saveBtn.textContent = '📝 計画を保存';
  const msg = document.getElementById('spFormMessage');
  if (msg) msg.textContent = '';
}

async function submitStudyPlan() {
  const msg = document.getElementById('spFormMessage');
  const btn = document.getElementById('spSaveBtn');
  if (!btn || btn.disabled) return;
  if (msg) { msg.textContent = ''; msg.style.color = '#a1a1aa'; }

  const wrap = document.getElementById('spFormWrap');
  const editId = wrap && wrap.dataset.editId ? parseInt(wrap.dataset.editId, 10) : null;

  const title = document.getElementById('spTitle').value.trim();
  const subject = document.getElementById('spSubject').value;
  const material = document.getElementById('spMaterial').value.trim();
  const start_date = document.getElementById('spStart').value;
  const end_date = document.getElementById('spEnd').value;
  const target_minutes_raw = document.getElementById('spTargetMin').value;
  const target_pages_raw = document.getElementById('spTargetPages').value;
  const color = document.getElementById('spColor').value;
  const note = document.getElementById('spNote').value.trim();

  if (!title) { if (msg) { msg.textContent = 'タイトルは必須です'; msg.style.color = '#fca5a5'; } return; }
  if (!subject) { if (msg) { msg.textContent = '科目を選択してください'; msg.style.color = '#fca5a5'; } return; }
  if (!start_date || !end_date) { if (msg) { msg.textContent = '開始日と終了日を入力してください'; msg.style.color = '#fca5a5'; } return; }
  if (end_date < start_date) { if (msg) { msg.textContent = '終了日は開始日以降にしてください'; msg.style.color = '#fca5a5'; } return; }

  const body = {
    title, subject,
    material: material || undefined,
    start_date, end_date,
    target_minutes: target_minutes_raw ? parseInt(target_minutes_raw, 10) : undefined,
    target_pages: target_pages_raw ? parseInt(target_pages_raw, 10) : undefined,
    color, note: note || undefined,
  };

  btn.disabled = true;
  btn.textContent = '保存中...';
  try {
    if (editId) {
      await slApiFetch(`/api/study-plans/${encodeURIComponent(editId)}`, { method: 'PUT', body: JSON.stringify(body) });
    } else {
      await slApiFetch('/api/study-plans', { method: 'POST', body: JSON.stringify(body) });
    }
    if (msg) { msg.textContent = '✅ 保存しました！'; msg.style.color = '#86efac'; }
    clearSpForm();
    document.getElementById('spFormWrap').style.display = 'none';
    await loadMyStudyPlans();
  } catch (e) {
    if (msg) { msg.textContent = '❌ ' + (e.message || '保存に失敗しました'); msg.style.color = '#fca5a5'; }
  } finally {
    btn.disabled = false;
    btn.textContent = editId ? '📝 計画を更新' : '📝 計画を保存';
  }
}

async function loadMyStudyPlans() {
  const list = document.getElementById('spPlanList');
  if (!list) return;
  try {
    const data = await slApiFetch('/api/study-plans/me');
    const plans = data.plans || [];
    _spLastPlans = plans;  // Frontend M-5: editStudyPlan の再 fetch 不要
    // 学習記録の material datalist 更新 (UX M-3: 表記揺れ対策)
    const dl = document.getElementById('slMaterialDatalist');
    if (dl) {
      const materials = Array.from(new Set(plans.filter(p => p.material).map(p => p.material)));
      dl.innerHTML = materials.map(m => `<option value="${escapeHtml(m)}">`).join('');
    }
    if (!plans.length) {
      list.innerHTML = '<div style="text-align:center; color:#71717a; padding:1.5rem; background:rgba(0,0,0,0.2); border-radius:10px;">📝 まだ計画がありません。「+ 新しい計画を追加」から第一歩を！</div>';
      return;
    }
    // active / completed / archived 分類
    const active = plans.filter(p => p.status === 'active');
    const completed = plans.filter(p => p.status === 'completed');
    const archived = plans.filter(p => p.status === 'archived');
    list.innerHTML = `
      ${renderSpPlanGroup('🎯 進行中', active, '#fbbf24')}
      ${renderSpPlanGroup('✅ 完了', completed, '#34d399')}
      ${archived.length ? renderSpPlanGroup('📦 アーカイブ', archived, '#71717a') : ''}
    `;
    // bind buttons
    list.querySelectorAll('.sp-edit-btn').forEach(b => b.addEventListener('click', () => editStudyPlan(b.getAttribute('data-id'))));
    list.querySelectorAll('.sp-diag-btn').forEach(b => b.addEventListener('click', () => diagStudyPlanWithAi(b.getAttribute('data-id'))));
    list.querySelectorAll('.sp-delete-btn').forEach(b => b.addEventListener('click', () => deleteStudyPlan(b.getAttribute('data-id'))));
    list.querySelectorAll('.sp-status-btn').forEach(b => b.addEventListener('click', () => changeStudyPlanStatus(b.getAttribute('data-id'), b.getAttribute('data-status'))));
  } catch (e) {
    console.error('loadMyStudyPlans failed:', e);
    list.innerHTML = `<div style="text-align:center; color:#fca5a5; padding:1rem;">⚠️ 計画の読み込みに失敗しました (${escapeHtml(e.message || '')}) <button onclick="loadMyStudyPlans()" style="margin-left:0.5rem; background:rgba(99,102,241,0.2); border:0; color:#c7d2fe; padding:0.3rem 0.6rem; border-radius:6px; cursor:pointer;">再試行</button></div>`;
  }
}

function renderSpPlanGroup(label, plans, accentColor) {
  if (!plans.length) return '';
  const cards = plans.map(p => {
    const today = _slJstDate(0);
    const remainDays = Math.max(0, Math.ceil((new Date(p.end_date) - new Date(today)) / 86400000));
    const totalDays = Math.max(1, Math.ceil((new Date(p.end_date) - new Date(p.start_date)) / 86400000) + 1);
    const elapsedDays = Math.max(0, Math.min(totalDays, Math.ceil((new Date(today) - new Date(p.start_date)) / 86400000) + 1));
    const dayPct = Math.round(elapsedDays / totalDays * 100);
    const minPct = p.progress_minutes_pct;
    const pagePct = p.progress_pages_pct;
    return `
      <div style="background:rgba(255,255,255,0.04); border-left:4px solid ${escapeHtml(p.color)}; border-radius:8px; padding:0.85rem; margin-bottom:0.6rem;">
        <div style="display:flex; justify-content:space-between; align-items:start; margin-bottom:0.4rem;">
          <div style="flex:1;">
            <div style="font-weight:700; color:#e4e4e7; font-size:0.95rem;">${escapeHtml(p.title)}</div>
            <div style="font-size:0.78rem; color:#a1a1aa; margin-top:0.2rem;">
              <span style="background:rgba(99,102,241,0.2); color:#c7d2fe; padding:0.1rem 0.4rem; border-radius:4px; font-size:0.72rem;">${escapeHtml(p.subject)}</span>
              ${p.material ? `<span style="margin-left:0.3rem;">${escapeHtml(p.material)}</span>` : ''}
            </div>
            <div style="font-size:0.75rem; color:#71717a; margin-top:0.2rem;">
              ${escapeHtml(p.start_date)} 〜 ${escapeHtml(p.end_date)}
              ${p.status === 'active' ? `<span style="color:${remainDays <= 7 ? '#fca5a5' : '#a1a1aa'}; margin-left:0.5rem;">残り ${remainDays} 日</span>` : ''}
            </div>
          </div>
          <div style="display:flex; gap:0.3rem;">
            <button data-id="${p.id}" class="sp-edit-btn" aria-label="編集" title="編集" style="background:none; border:0; color:#a1a1aa; cursor:pointer; font-size:0.9rem;">✏️</button>
            ${p.status === 'active' ? `<button data-id="${p.id}" class="sp-diag-btn" aria-label="AI診断" title="AI が進捗を診断" style="background:none; border:0; color:#a78bfa; cursor:pointer; font-size:0.9rem;">🤖</button>` : ''}
            ${p.status === 'active' ? `<button data-id="${p.id}" data-status="completed" class="sp-status-btn" aria-label="完了にする" title="完了にする" style="background:none; border:0; color:#34d399; cursor:pointer; font-size:0.9rem;">✅</button>` : ''}
            <button data-id="${p.id}" class="sp-delete-btn" aria-label="削除" title="削除" style="background:none; border:0; color:#71717a; cursor:pointer; font-size:0.9rem;">🗑</button>
          </div>
        </div>
        ${minPct !== null && minPct !== undefined ? `
          <div style="margin-top:0.4rem;">
            <div style="display:flex; justify-content:space-between; font-size:0.72rem; color:#a1a1aa; margin-bottom:0.2rem;">
              <span>勉強時間 ${p.actual_minutes}/${p.target_minutes}分</span>
              <span style="color:${minPct >= dayPct ? '#86efac' : '#fca5a5'};">${minPct}% (経過 ${dayPct}%)</span>
            </div>
            <div style="background:rgba(255,255,255,0.05); border-radius:4px; height:6px; overflow:hidden; position:relative;">
              <div style="background:linear-gradient(90deg,#6366f1,#ec4899); height:100%; width:${Math.min(100, minPct)}%;"></div>
              <div style="position:absolute; top:0; left:${Math.min(100, dayPct)}%; width:1px; height:100%; background:#fbbf24;"></div>
            </div>
          </div>` : (p.actual_minutes > 0 || p.actual_pages > 0) ? `
          <div style="margin-top:0.4rem; font-size:0.75rem; color:#a1a1aa;">
            実績: ${p.actual_minutes}分${p.actual_pages ? ' / ' + p.actual_pages + 'p' : ''} <span style="font-size:0.7rem; color:#71717a;">(目標未設定)</span>
          </div>` : ''}
        ${pagePct !== null && pagePct !== undefined ? `
          <div style="margin-top:0.4rem;">
            <div style="display:flex; justify-content:space-between; font-size:0.72rem; color:#a1a1aa; margin-bottom:0.2rem;">
              <span>ページ ${p.actual_pages}/${p.target_pages}p</span>
              <span style="color:${pagePct >= dayPct ? '#86efac' : '#fca5a5'};">${pagePct}%</span>
            </div>
            <div style="background:rgba(255,255,255,0.05); border-radius:4px; height:6px; overflow:hidden;">
              <div style="background:linear-gradient(90deg,#10b981,#34d399); height:100%; width:${Math.min(100, pagePct)}%;"></div>
            </div>
          </div>` : ''}
        ${p.note ? `<div style="font-size:0.78rem; color:#d4d4d8; margin-top:0.4rem; padding:0.4rem 0.5rem; background:rgba(0,0,0,0.2); border-radius:6px;">${escapeHtml(p.note)}</div>` : ''}
      </div>`;
  }).join('');
  return `
    <div style="margin-bottom:1rem;">
      <div style="font-size:0.85rem; color:${accentColor}; font-weight:700; margin-bottom:0.5rem;">${label} (${plans.length})</div>
      ${cards}
    </div>`;
}

async function editStudyPlan(id) {
  // load existing plan, populate form (cache 優先 / Frontend M-5)
  try {
    let plan = _spLastPlans.find(p => String(p.id) === String(id));
    if (!plan) {
      const data = await slApiFetch('/api/study-plans/me');
      _spLastPlans = data.plans || [];
      plan = _spLastPlans.find(p => String(p.id) === String(id));
    }
    if (!plan) { alert('計画が見つかりません'); return; }
    document.getElementById('spTitle').value = plan.title;
    document.getElementById('spSubject').value = plan.subject;
    document.getElementById('spMaterial').value = plan.material || '';
    document.getElementById('spStart').value = plan.start_date;
    document.getElementById('spEnd').value = plan.end_date;
    document.getElementById('spTargetMin').value = plan.target_minutes || '';
    document.getElementById('spTargetPages').value = plan.target_pages || '';
    document.getElementById('spColor').value = plan.color || '#6366f1';
    document.getElementById('spNote').value = plan.note || '';
    const wrap = document.getElementById('spFormWrap');
    wrap.dataset.editId = id;
    wrap.style.display = '';
    document.getElementById('spSaveBtn').textContent = '📝 計画を更新';
    wrap.scrollIntoView({ behavior: 'smooth', block: 'center' });
  } catch (e) {
    alert('読み込みに失敗: ' + (e.message || ''));
  }
}

async function deleteStudyPlan(id) {
  if (!confirm('この計画を削除しますか？\n（一度削除すると元に戻せません）')) return;
  try {
    await slApiFetch(`/api/study-plans/${encodeURIComponent(id)}`, { method: 'DELETE' });
    await loadMyStudyPlans();
  } catch (e) {
    alert('削除に失敗: ' + (e.message || ''));
  }
}

async function changeStudyPlanStatus(id, newStatus) {
  if (newStatus === 'completed' && !confirm('この計画を完了にしますか？')) return;
  try {
    await slApiFetch(`/api/study-plans/${encodeURIComponent(id)}`, {
      method: 'PUT',
      body: JSON.stringify({ status: newStatus }),
    });
    await loadMyStudyPlans();
  } catch (e) {
    alert('変更に失敗: ' + (e.message || ''));
  }
}


// ==========================================================================
// 📨 メッセージ受信箱 (Phase 3 - 全生徒対象)
// ==========================================================================
let _msgPollTimer = null;

// ISO 文字列を JST 'YYYY-MM-DD HH:MM' に変換 (UTC 表示ズレ防止 / UX C-1)
function _fmtJstYMDHM(s) {
  if (!s) return '';
  try {
    const iso = String(s);
    const d = new Date(iso.endsWith('Z') || /[+-]\d\d:?\d\d$/.test(iso) ? iso : iso + 'Z');
    if (isNaN(d)) return String(s).slice(0, 16).replace('T', ' ');
    const fmt = new Intl.DateTimeFormat('ja-JP', { timeZone: 'Asia/Tokyo', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false });
    return fmt.format(d).replace(/\//g, '-');
  } catch { return String(s).slice(0, 16).replace('T', ' '); }
}

function initMessages() {
  loadMyMessages();
  // 60秒に1回 unread count を polling (タブ非アクティブ時は停止)
  const startPoll = () => {
    if (_msgPollTimer) return;
    _msgPollTimer = setInterval(refreshUnreadBadge, 60000);
  };
  const stopPoll = () => {
    if (_msgPollTimer) { clearInterval(_msgPollTimer); _msgPollTimer = null; }
  };
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) stopPoll();
    else { startPoll(); refreshUnreadBadge(); }
  });
  if (!document.hidden) startPoll();
}

async function refreshUnreadBadge() {
  try {
    const data = await slApiFetch('/api/messages/me/unread-count');
    updateUnreadBadge(data.unread_count || 0);
  } catch (e) { /* silent */ }
}

function updateUnreadBadge(count) {
  const badge = document.getElementById('msgUnreadBadge');
  if (!badge) return;
  if (count > 0) {
    badge.textContent = count > 99 ? '99+' : count;
    badge.style.display = '';
  } else {
    badge.style.display = 'none';
  }
}

async function loadMyMessages() {
  const list = document.getElementById('msgList');
  if (!list) return;
  list.innerHTML = '<div style="text-align:center; color:#71717a; padding:1rem;">📨 読み込み中...</div>';
  try {
    const data = await slApiFetch('/api/messages/me?limit=50');
    const msgs = data.messages || [];
    updateUnreadBadge(data.unread_count || 0);
    if (!msgs.length) {
      list.innerHTML = '<div style="text-align:center; color:#71717a; padding:1.5rem; background:rgba(0,0,0,0.2); border-radius:10px;">📭 メッセージはまだありません</div>';
      return;
    }
    list.innerHTML = msgs.map(m => {
      const unreadBorder = m.is_unread ? 'border-left:4px solid #ec4899;' : 'border-left:4px solid rgba(255,255,255,0.05);';
      const dotBadge = m.is_unread ? '<span class="msg-unread-dot" style="display:inline-block; width:8px; height:8px; background:#ec4899; border-radius:50%; margin-right:0.4rem; vertical-align:middle;"></span>' : '';
      return `
        <div data-msg-id="${m.id}" data-unread="${m.is_unread ? '1' : '0'}" class="msg-item" style="background:rgba(255,255,255,0.04); ${unreadBorder} border-radius:8px; padding:0.85rem; margin-bottom:0.6rem; cursor:pointer;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.3rem;">
            <div style="font-weight:700; color:#c7d2fe; font-size:0.9rem;">${dotBadge}${escapeHtml(m.subject || 'お知らせ')}</div>
            <div style="font-size:0.72rem; color:#71717a;">${escapeHtml(_fmtJstYMDHM(m.created_at))}</div>
          </div>
          <div class="msg-body" style="font-size:0.85rem; color:#d4d4d8; white-space:pre-wrap; max-height:3em; overflow:hidden; text-overflow:ellipsis; transition:max-height 0.3s;">${escapeHtml(m.body)}</div>
        </div>`;
    }).join('');
    list.querySelectorAll('.msg-item').forEach(el => {
      el.addEventListener('click', async () => {
        const body = el.querySelector('.msg-body');
        const expanded = el.dataset.expanded === '1';
        if (expanded) {
          body.style.maxHeight = '3em';
          el.dataset.expanded = '0';
        } else {
          body.style.maxHeight = '60em';
          el.dataset.expanded = '1';
          // 既読化
          if (el.dataset.unread === '1') {
            const id = el.getAttribute('data-msg-id');
            try {
              await slApiFetch(`/api/messages/me/${encodeURIComponent(id)}/read`, { method: 'POST' });
              el.dataset.unread = '0';
              el.style.borderLeft = '4px solid rgba(255,255,255,0.05)';
              const dot = el.querySelector('.msg-unread-dot');
              if (dot) dot.remove();
              await refreshUnreadBadge();
            } catch (e) { /* silent */ }
          }
        }
      });
    });
  } catch (e) {
    console.error('loadMyMessages failed:', e);
    list.innerHTML = `<div style="text-align:center; color:#fca5a5; padding:1rem;">⚠️ メッセージ読み込み失敗 (${escapeHtml(e.message || '')}) <button id="msgRetryBtn" style="margin-left:0.5rem; background:rgba(99,102,241,0.2); border:0; color:#c7d2fe; padding:0.3rem 0.6rem; border-radius:6px; cursor:pointer;">再試行</button></div>`;
    const retryBtn = document.getElementById('msgRetryBtn');
    if (retryBtn) retryBtn.addEventListener('click', loadMyMessages);
  }
}


// ==========================================================================
// 📩 コース申込問い合わせ (一般生徒の CTA ボタン)
// ==========================================================================
function bindCourseInquiryButtons(scope) {
  const root = scope || document;
  root.querySelectorAll('.course-inquiry-btn').forEach(btn => {
    if (btn._inquiryBound) return;
    btn._inquiryBound = true;
    btn.addEventListener('click', async () => {
      if (btn.disabled) return;
      const course = btn.getAttribute('data-course') || 'kokuritsu_nankan';
      const source = btn.getAttribute('data-source') || '';
      const msgEl = btn.parentElement.querySelector('.course-inquiry-msg');
      // 確認ダイアログ (誤タップ防止)
      const noteRaw = prompt('塾長への伝言があれば入力してください (任意・最大500文字)\n\n空欄のまま OK で送信できます。', '');
      if (noteRaw === null) return; // キャンセル
      btn.disabled = true;
      const originalText = btn.textContent;
      btn.textContent = '送信中...';
      try {
        const data = await slApiFetch('/api/student/course-inquiry', {
          method: 'POST',
          body: JSON.stringify({ course, note: (noteRaw || ('mypage:' + source)).trim() }),
        });
        if (msgEl) {
          msgEl.innerHTML = `<span style="color:#86efac;">✅ ${escapeHtml(data.message || 'お問い合わせを受け付けました')}</span>`;
        }
        btn.textContent = '✅ 送信済み';
        btn.style.background = 'rgba(134,239,172,0.2)';
        btn.style.color = '#86efac';
        btn.style.boxShadow = 'none';
        // refresh unread badge (確認 message が届いた)
        if (typeof refreshUnreadBadge === 'function') refreshUnreadBadge();
      } catch (e) {
        if (msgEl) msgEl.innerHTML = `<span style="color:#fca5a5;">❌ ${escapeHtml(e.message || '送信に失敗しました')}</span>`;
        btn.disabled = false;
        btn.textContent = originalText;
      }
    });
  });
}
