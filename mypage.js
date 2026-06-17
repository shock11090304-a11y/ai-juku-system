// ==========================================================================
// Student Mypage - Gamified Learning Dashboard
// ==========================================================================

const KEYS = {
  STUDENTS: 'ai_juku_students',
  CURRENT: 'ai_juku_current_student',
  STATS: 'ai_juku_stats',
  MYPAGE: 'ai_juku_mypage',
};

// ==========================================================================
// 学習管理機能 (学習記録・カリキュラム・模試分析・弱点プリント) アクセス判定
// 新プラン体系 2026-05-06 (通塾生優遇方針):
//   - course='kokuritsu_nankan' (本クラス所属生徒) → 解放
//   - plan='premium' (¥19,800) / 'family' (¥39,800) / 'founder_special' (¥14,500 永年) → 解放
//   - plan='student_addon' (通塾生 ¥5,000・招待制限定) → 解放 (塾長指示 2026-05-06)
//   - plan='standard' (旧 ¥24,980・募集停止) のみ NG
// ==========================================================================
const _STUDY_MGMT_PLANS = ['premium', 'family', 'founder_special', 'student_addon'];
function _canUseStudyMgmt(student) {
  if (!student) return false;
  if (student.course === 'kokuritsu_nankan') return true;
  const plan = String(student.plan || '').toLowerCase();
  return _STUDY_MGMT_PLANS.indexOf(plan) >= 0;
}
// 塾長との双方向メッセージ・授業ファイル送受信は本クラス所属生徒のみ (有料プランは対象外)
function _canUseTeacherMessaging(student) {
  return !!(student && student.course === 'kokuritsu_nankan');
}

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
  let currentId = JSON.parse(localStorage.getItem(KEYS.CURRENT) || 'null');
  // 🔑 2026-06-14 [trust-identity] ai_juku_session_student (= サーバ署名トークンを
  //   /api/auth/me で検証した本人・氏名込み) を常に権威ソースにする。これがあれば戻り値は
  //   必ず本人 (氏名等は session で上書き) になり、表示ポインタずれによる別生徒の氏名表示
  //   (室坂海來さん事故) を構造的に排除する。ハードリロードや非同期 /api/auth/me 解決を
  //   待たずに開いた瞬間から本人表示。書き戻しは初回のみ (定常は read-only)。
  try {
    const sess = JSON.parse(localStorage.getItem('ai_juku_session_student') || 'null');
    if (sess && sess.id != null) {
      const idx = students.findIndex(s => s && s.id === sess.id);
      if (currentId !== sess.id || idx < 0) {
        if (idx >= 0) students[idx] = { ...students[idx], ...sess };
        else students.push(sess);
        localStorage.setItem(KEYS.STUDENTS, JSON.stringify(students));
        localStorage.setItem(KEYS.CURRENT, JSON.stringify(sess.id));
      }
      // 戻り値は write 有無に関わらず常に「本人」を返す (氏名/学年/志望校は session を優先)。
      const base = students.find(s => s && s.id === sess.id) || {};
      return { ...base, ...sess };
    }
  } catch (e) {}
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

// 🔰 2026-06-11 塾長指示 (低学力層オンボーディング改修): 旧コードは新規生徒に
// 架空の進捗 (xp680/streak7/今日45分/週次グラフ) を seed していた。何もしていないのに
// 「7日連続学習・Lv.4」が出る嘘は信頼を壊すため廃止し、正直に 0 から開始する。
// streak/XP は「コーチの今日の一手」の ✅達成 で実際に増える本物の値になった。
function _zeroMypageData() {
  return {
    xp: 0,
    streak: 0,
    streakHistory: [0, 0, 0, 0, 0, 0, 0],
    todayMinutes: 0,
    todayQuestions: 0,
    weeklyMinutes: [0, 0, 0, 0, 0, 0, 0],
    lastLogin: todayKeyJST(),
  };
}

function getMypageData() {
  const key = mypageKeyForCurrentStudent();
  const saved = JSON.parse(localStorage.getItem(key) || 'null');
  if (saved) {
    // 旧 seed の架空値が localStorage に保存済みの既存生徒を 1 回だけ 0 にリセット。
    // 署名 = streak7 + 今日45分 + 固定週次配列の完全一致。xp は旧クエスト機能 (2026-05-15 廃止)
    // が ±変更していた時期があるため署名に含めない (review 指摘: xp 条件があると当時の
    // クエスト操作者だけ偽 streak/グラフが残る)。streak/todayMinutes/weeklyMinutes に
    // 書き込む経路は seed 以外に存在しなかったことを git 履歴で確認済み → 誤爆しない。
    const _legacySeed = saved.streak === 7 && saved.todayMinutes === 45 &&
      Array.isArray(saved.weeklyMinutes) && saved.weeklyMinutes.join(',') === '60,45,80,30,90,75,45';
    if (_legacySeed) {
      const reset = _zeroMypageData();
      localStorage.setItem(key, JSON.stringify(reset));
      return reset;
    }
    return saved;
  }
  const data = _zeroMypageData();
  localStorage.setItem(key, JSON.stringify(data));
  return data;
}

// 🔰 初回訪問日の記録 (新規生徒判定用・比較セクションの「最下位通告」を初週は出さない)
function _firstSeenKey() { return 'aj-first-seen:' + mypageKeyForCurrentStudent(); }
function _markFirstSeen() {
  try { if (!localStorage.getItem(_firstSeenKey())) localStorage.setItem(_firstSeenKey(), todayKeyJST()); } catch (_) { /* noop */ }
}
function _isFreshStudent(days = 7) {
  try {
    const first = localStorage.getItem(_firstSeenKey());
    if (!first) return true;
    const diff = (new Date(todayKeyJST()) - new Date(first)) / 86400000;
    return diff < days;
  } catch (_) { return false; }
}

function saveMypageData(data) {
  localStorage.setItem(mypageKeyForCurrentStudent(), JSON.stringify(data));
}

// ==========================================================================
// Render
// ==========================================================================
function render() {
  const student = getCurrentStudent();
  _markFirstSeen(); // 🔰 新規生徒判定 (比較セクションの初週ゲート) 用に初回訪問日を記録
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

  // Quests: 塾長指示 2026-05-15 でクエスト機能廃止

  // Today stats
  // 学習管理機能 (kokuritsu_nankan / premium 以上) の生徒は CTA の refreshSlQuickCtaToday が
  // /api/study-logs/me から実データを書き込むので、ここでは demo を出さず "—" 表示にして
  // demo "45" が一瞬出る flicker を防ぐ。getCurrentStudent() は localStorage の旧データなので
  // AuthGuard.getStudent() (server から取得した最新セッション) を優先。
  const todayMinEl = document.getElementById('todayMinutes');
  if (todayMinEl) {
    const authStudent = (window.AuthGuard && window.AuthGuard.getStudent && window.AuthGuard.getStudent()) || null;
    if (authStudent && _canUseStudyMgmt(authStudent)) {
      todayMinEl.textContent = '—';
    } else {
      todayMinEl.textContent = data.todayMinutes;
    }
  }
  document.getElementById('todayQ').textContent = data.todayQuestions;
  // todayDone / todayXp は塾長指示 2026-05-15 でクエスト機能廃止に伴い削除済
  // AI 質問数を backend events から取得して上書き (端末跨ぎでも正確)
  _refreshAiQuestionsFromBackend();

  // Weekly chart
  renderWeeklyChart(data.weeklyMinutes);

  // 🏆 アチーブメントを実データで再判定 (2026-06-11: 静的 HTML の架空「獲得済み」を廃止)
  refreshAchievements(data);

  // 🔰 シンプルモード適用 (Phase 2)。✅達成→render() のたびに開放 tier を再評価。
  // AuthGuard の student 取得 (created_at) が初回ロードで遅れるケースに備え 1.5s 後にも 1 回再適用。
  applyUiLevel();
  if (!window._ajUiLevelRetried) {
    window._ajUiLevelRetried = true;
    setTimeout(applyUiLevel, 1500);
    setTimeout(applyUiLevel, 4000); // 低速回線で /api/auth/me が遅れるケースの取りこぼし防止
  }

  // Motivation
  rotateMotivation();
}

// ==========================================================================
// 🏆 アチーブメント (2026-06-11 塾長指示: 偽の「4/12 獲得」固定表示を実データ判定に置換)
//   - ルール判定できるもの (streak 系) は getMypageData() の実値から自動判定
//   - イベント由来 (初質問など) は _unlockAchievement(key) で生徒ごとに永続化
//   - 判定材料が無いものは locked のまま (嘘の点灯はしない)
// ==========================================================================
const _ACH_RULES = {
  streak3: (d) => (d.streak || 0) >= 3,
  streak7: (d) => (d.streak || 0) >= 7,
};
function _achStoreKey(k) { return 'aj-ach:' + k + ':' + mypageKeyForCurrentStudent(); }
function refreshAchievements(data) {
  try {
    const els = document.querySelectorAll('.achievement[data-ach]');
    if (!els.length) return;
    let unlocked = 0;
    els.forEach((el) => {
      const k = el.dataset.ach;
      let on = false;
      try { on = localStorage.getItem(_achStoreKey(k)) === '1'; } catch (_) { /* noop */ }
      const rule = _ACH_RULES[k];
      if (!on && rule && data && rule(data)) {
        on = true;
        // 一度獲得したバッジは streak が途切れても剥奪しない (アチーブメントの普遍ルール・review 指摘)
        try { localStorage.setItem(_achStoreKey(k), '1'); } catch (_) { /* noop */ }
      }
      el.classList.toggle('unlocked', on);
      el.classList.toggle('locked', !on);
      const icon = el.querySelector('.ach-icon');
      if (icon) icon.textContent = on ? (el.dataset.achIcon || '🏅') : '🔒';
      if (on) unlocked++;
    });
    const prog = document.getElementById('achProgress');
    // 0 個のときは「0/8 獲得」より HTML 初期文言「これから獲得しよう」の方が新規生徒に冷たくない
    if (prog && unlocked > 0) prog.textContent = unlocked + '/' + els.length + ' 獲得';
  } catch (_) { /* 表示系のみ・失敗しても他機能に影響させない */ }
}
function _unlockAchievement(k) {
  try {
    if (localStorage.getItem(_achStoreKey(k)) === '1') return;
    localStorage.setItem(_achStoreKey(k), '1');
    refreshAchievements(getMypageData());
  } catch (_) { /* noop */ }
}

// AI 質問数を /api/usage/me から取得して #todayQ を上書き
async function _refreshAiQuestionsFromBackend() {
  try {
    const token = (window.AuthGuard && window.AuthGuard.getToken && window.AuthGuard.getToken()) || localStorage.getItem('ai_juku_session_token');
    if (!token) return;
    const apiBase = (window.location.origin.includes(':8090') || window.location.origin.includes('localhost:8090'))
      ? 'http://localhost:8000' : window.location.origin;
    const res = await fetch(apiBase + '/api/usage/me', { headers: { 'Authorization': 'Bearer ' + token } });
    if (!res.ok) return;
    const data = await res.json();
    const aiq = data.ai_questions || {};
    const todayEl = document.getElementById('todayQ');
    if (todayEl && typeof aiq.today === 'number') todayEl.textContent = aiq.today;
    // 🏆 初質問アチーブメント: 実際に AI へ質問した実績がある生徒のみ点灯 (2026-06-11)
    if ((Number(aiq.today) || 0) > 0 || (Number(aiq.total) || 0) > 0) _unlockAchievement('first_question');
  } catch (e) { console.warn('[AI質問数] backend 同期失敗:', e); }
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

// renderQuests / toggleQuest は塾長指示 2026-05-15 でクエスト機能廃止に伴い削除

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
  // 🧒 塾長プレビュー (2026-06-04): プレビュー閲覧を生徒の活動ログに記録しない
  if (typeof window.ajPreviewMode === 'function' && window.ajPreviewMode()) return;
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
// 10日間トライアル体験導線 (Trial Onboarding) は塾長指示 2026-05-15 で削除
// (本契約生徒の mypage に体験プログラムを表示する意味がないため)
// ==========================================================================
// (Trial Onboarding 関連の全関数を削除: getTrialState / saveTrialState /
//  getTrialDayNumber / renderTrialOnboarding / bindTrialOnboarding / TRIAL_DAYS / TRIAL_KEY)
// 本契約生徒の mypage には体験プログラムを表示しないため不要

document.addEventListener('DOMContentLoaded', () => {
  // 🛡️ 2026-05-13 塾長指示「学習管理が絶対に消えない」: MutationObserver で能動的に防御
  // 万一どこかのコードが section.style.display='none' に setしても自動で復元する。
  // ブラウザ拡張・Service Worker・第三者 JS・将来追加コードの暴走でも消えない設計。
  try {
    _installNeverHideGuard([
      '.study-log-section',
      '.study-log-quick-cta',
      '.study-plan-section',
      '.curriculum-section',
      '.exam-section',
    ]);
  } catch (e) { console.error('never-hide guard install failed:', e); }

  // 各初期化を独立に try/catch して、1つの失敗で以降の初期化が連鎖停止しないようにする
  try { render(); } catch (e) { console.error('render failed:', e); }
  try { logActivity('mypage_view'); } catch (e) { console.error('logActivity failed:', e); }
  try { initStudyLog(); } catch (e) { console.error('initStudyLog failed:', e); }
  try { initStudyLogQuickCta(); } catch (e) { console.error('initStudyLogQuickCta failed:', e); }
  try { initExamResults(); } catch (e) { console.error('initExamResults failed:', e); }
  try { initCurriculum(); } catch (e) { console.error('initCurriculum failed:', e); }
  try { initStudyPlan(); } catch (e) { console.error('initStudyPlan failed:', e); }
  try { initMessages(); } catch (e) { console.error('initMessages failed:', e); }
  try { initReferralSection(); } catch (e) { console.error('initReferralSection failed:', e); }
  try { initCustomGptBlock(); } catch (e) { console.error('initCustomGptBlock failed:', e); }
  try { initHomeworkSection(); } catch (e) { console.error('initHomeworkSection failed:', e); }
  try { initGrammarDrillSection(); } catch (e) { console.error('initGrammarDrillSection failed:', e); }
  try { initComparisonSection(); } catch (e) { console.error('initComparisonSection failed:', e); }
});

// 🤖 ai-juku 公式 Custom GPT 案内 block (2026-05-23 塾長指示「C: 生徒画面に Custom GPT 案内」)
// 生徒の course/grade に応じて 6 体から推奨表示・ChatGPT 連携で継続率向上
const CUSTOM_GPT_DATA = [
  {
    id: 'todai_math_60days',
    name: 'ai-juku 東大数学 60日 master',
    desc: '東大理系数学 6 問形式の頻出 30 パターン × 60 日カリキュラム',
    url: 'https://chatgpt.com/g/g-6a00ba927598819180c6f2e323d0b275-ai-juku-dong-da-shu-xue-60ri-master',
    icon: '📐', tags: ['todai', 'math', 'rikei']
  },
  {
    id: 'soukei_eigo_master',
    name: 'ai-juku 早慶英語 master',
    desc: '早慶 (政経/法/商/文/医) 英語の構文 30 + 語彙 50 × 60 日特化',
    url: 'https://chatgpt.com/g/g-6a00b7f0a90c81919f0c32599d1e0354-ai-juku-zao-qing-ying-yu-master',
    icon: '📝', tags: ['waseda', 'keio', 'english']
  },
  {
    id: 'kyotsu_test_plus10',
    name: 'ai-juku 共通テスト 偏差値+10 道場',
    desc: '共通テスト 6 科目 (英数国理社) を 90 日で偏差値 +10 を目指す',
    url: 'https://chatgpt.com/g/g-6a00b8d744f88191b7d9c08e5ebaf5b9-ai-juku-gong-tong-tesuto-pian-chai-zhi-10-dao-chang',
    icon: '🎯', tags: ['kyotsu', 'all']
  },
  {
    id: 'eiken_pre1_60days',
    name: 'ai-juku 英検準1級 60日',
    desc: '英検準1級 5 領域 (R/L/W/S/語彙) を 60 日で総合合格レベルへ',
    url: 'https://chatgpt.com/g/g-6a00b93ea954819198b4120cc47f1b36-ai-juku-ying-jian-zhun-1ji-60ri',
    icon: '🎓', tags: ['eiken', 'english']
  },
  {
    id: 'physics_core_image_master',
    name: 'ai-juku 物理 コアイメージ master',
    desc: '高校物理 5 単元 (力学/熱/波動/電磁気/原子) をコアイメージで腑に落とす',
    url: 'https://chatgpt.com/g/g-6a00c05794d8819186beab1ded27ae27-ai-juku-wu-li-koaimesi-master',
    icon: '⚛️', tags: ['physics', 'rikei']
  },
  {
    id: 'kobun_kanbun_master',
    name: 'ai-juku 古文・漢文 master',
    desc: '共テ古典 (古文/漢文) を文法暗記なしで読解力で攻略',
    url: 'https://chatgpt.com/g/g-6a00b256abd481919c5f7323e16677f8-ai-juku-gu-wen-han-wen-master',
    icon: '📜', tags: ['kobun', 'kanbun', 'japanese']
  }
];

function _recommendCustomGpts() {
  // 生徒の course/eikenGrade から推奨 GPT を抽出 (なければ全 6 体表示)
  // 3 視点 review fix: window.STATE.student は未定義 → getCurrentStudent() (localStorage 経由) を使う
  try {
    const stu = (typeof getCurrentStudent === 'function') ? getCurrentStudent() : {};
    const course = String(stu.course || stu.target_school || '').toLowerCase();
    const grade = String(stu.eiken_grade || stu.target_university || stu.grade || '').toLowerCase();
    const tags = new Set();
    if (course.includes('todai') || grade.includes('todai')) { tags.add('todai'); tags.add('rikei'); }
    if (course.includes('keio') || course.includes('waseda') || grade.includes('keio') || grade.includes('waseda')) tags.add('keio');
    if (course.includes('eiken') || grade.includes('eiken') || grade.includes('gp1')) tags.add('eiken');
    if (course.includes('kyotsu') || grade.includes('kyotsu')) tags.add('kyotsu');
    if (course.includes('rikei') || course.includes('math') || course.includes('phys') || course.includes('chem')) tags.add('rikei');
    if (course.includes('bunkei') || course.includes('kobun') || course.includes('kanbun')) tags.add('japanese');
    if (tags.size === 0) return CUSTOM_GPT_DATA;
    const filtered = CUSTOM_GPT_DATA.filter(g => g.tags.some(t => tags.has(t)));
    return filtered.length >= 2 ? filtered : CUSTOM_GPT_DATA;
  } catch (e) {
    return CUSTOM_GPT_DATA;
  }
}

function initCustomGptBlock() {
  const section = document.getElementById('customGptSection');
  const list = document.getElementById('customGptList');
  const toggle = document.getElementById('customGptToggle');
  const body = document.getElementById('customGptBody');
  if (!section || !list) return;
  const gpts = _recommendCustomGpts();
  if (gpts.length === 0) { section.style.display = 'none'; return; }
  section.style.display = 'block';
  list.innerHTML = '';
  // utm 計測のため SID を取得 (3 視点 review fix: localStorage 経由)
  let sid = '';
  try {
    const stu = (typeof getCurrentStudent === 'function') ? getCurrentStudent() : {};
    sid = stu && stu.id != null ? String(stu.id) : '';
  } catch (_) {}
  gpts.forEach(g => {
    const utm = '?utm_source=ai_juku_mypage&utm_medium=custom_gpt_block&utm_campaign=' + encodeURIComponent(g.id) + (sid ? '&sid=' + encodeURIComponent(sid) : '');
    const a = document.createElement('a');
    a.href = g.url + utm;
    a.target = '_blank';
    a.rel = 'noopener noreferrer';
    a.dataset.gptId = g.id;
    a.style.cssText = 'display:flex;align-items:center;gap:0.7rem;padding:0.8rem 1rem;background:rgba(0,0,0,0.3);border:1px solid rgba(34,197,94,0.3);border-radius:10px;text-decoration:none;color:inherit;transition:transform 0.2s,border-color 0.2s;';
    a.onmouseover = () => { a.style.transform = 'translateY(-2px)'; a.style.borderColor = 'rgba(34,197,94,0.6)'; };
    a.onmouseout = () => { a.style.transform = ''; a.style.borderColor = 'rgba(34,197,94,0.3)'; };
    a.innerHTML = '<div style="font-size:1.3rem;flex-shrink:0;">' + g.icon + '</div>' +
      '<div style="flex:1;min-width:0;">' +
      '<div style="font-weight:700;color:#34d399;font-size:0.92rem;line-height:1.3;">' + _escapeHtml(g.name) + '</div>' +
      '<div style="color:#a1a1aa;font-size:0.78rem;margin-top:0.15rem;line-height:1.4;">' + _escapeHtml(g.desc) + '</div>' +
      '</div>' +
      '<div style="color:#34d399;flex-shrink:0;font-weight:700;">→</div>';
    // click event log (3 視点 review fix: logActivity は 1 引数のみ受け取るため fetch を直接コール)
    a.addEventListener('click', () => {
      try {
        const stu = (typeof getCurrentStudent === 'function') ? getCurrentStudent() : {};
        const meta = { gpt_id: g.id, source: 'mypage_block', url: g.url };
        fetch(`${BACKEND_URL}/api/activity/log`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ student_id: stu && stu.id, type: 'custom_gpt_click', meta }),
          keepalive: true
        }).catch(() => {});
      } catch (_) {}
    });
    list.appendChild(a);
  });
  // toggle (折りたたみ)
  if (toggle && body) {
    toggle.addEventListener('click', () => {
      const open = body.style.display !== 'none';
      body.style.display = open ? 'none' : 'block';
      toggle.textContent = open ? '▶ 展開する' : '▼ 折りたたむ';
      toggle.setAttribute('aria-expanded', open ? 'false' : 'true');
    });
  }
}

function _escapeHtml(s) {
  return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// 🛡️ 「絶対に消えない」能動的防御: MutationObserver で display:none を阻止
// 教育アプリの可用性として、学習管理セクションが消えた状態をユーザーに見せない
function _installNeverHideGuard(selectors) {
  if (!('MutationObserver' in window)) return;
  const targets = [];
  selectors.forEach(sel => {
    document.querySelectorAll(sel).forEach(el => targets.push({ el, sel }));
  });
  if (targets.length === 0) return;
  const observer = new MutationObserver((mutations) => {
    for (const m of mutations) {
      if (m.type !== 'attributes' || m.attributeName !== 'style') continue;
      const el = m.target;
      // display:none / visibility:hidden / opacity:0 を検出 → 復元
      const cs = window.getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility === 'hidden') {
        const sel = targets.find(t => t.el === el)?.sel || el.className;
        console.warn(`[never-hide-guard] 学習管理 ${sel} が hide されました → 自動復元`);
        el.style.display = '';
        el.style.visibility = '';
        // 監視用 event 記録 (デバッグ + 塾長の CEO ダッシュで可視化可能)
        try {
          if (window.AuthGuard?.getToken && navigator.sendBeacon) {
            const ev = JSON.stringify({
              event: 'study_mgmt_hide_blocked',
              selector: sel,
              ts: Date.now(),
              ua: navigator.userAgent.slice(0, 200),
            });
            navigator.sendBeacon('/api/events/client', ev);
          }
        } catch (_) {}
      }
    }
  });
  targets.forEach(({ el }) => {
    observer.observe(el, { attributes: true, attributeFilter: ['style', 'class'] });
  });
  console.info(`[never-hide-guard] ${targets.length} 学習管理セクションを能動監視中 (display:none 自動復元)`);
}

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
        text: '塾の友達に教えたい📣 AIコーチング — 入塾金¥10,000免除キャンペーン中！\n24時間 AI 質問対応・東大/京大レベルの問題AI自動生成。\n紹介で僕も¥3,000 OFF (Stripe 自動適用)',
      };
    }
    return {
      url,
      text: 'AIコーチング — 友達紹介で入塾金¥10,000免除！\n24時間 AI 質問対応・個別カリキュラム自動設計。\n\n👇 紹介URLから登録するとお得',
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
  wireShare('shareEmailBtn', s => `mailto:?subject=${encodeURIComponent('AIコーチング 紹介URL')}&body=${encodeURIComponent(s.text + '\n\n' + s.url)}`);

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

// 🔧 2026-05-14 塾長指示「[object Object] エラー修正」: FastAPI 422 validation の detail
// は配列形式で返ることがあり new Error(arr) が [object Object] 化する。整形 helper。
function _slFormatErrDetail(detail) {
  if (detail == null) return '';
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail.map(d => {
      if (typeof d === 'string') return d;
      if (d && typeof d === 'object') {
        const loc = Array.isArray(d.loc) ? d.loc.join('.') : (d.loc || '');
        const msg = d.msg || d.message || '';
        if (loc && msg) return `${loc}: ${msg}`;
        return msg || JSON.stringify(d);
      }
      return String(d);
    }).join('; ');
  }
  if (typeof detail === 'object') {
    return detail.msg || detail.message || JSON.stringify(detail);
  }
  return String(detail);
}

async function slApiFetch(path, options = {}) {
  // 🧒 塾長プレビュー (2026-06-04): ?preview_mode= 中は実 API を一切叩かない (no-op)。
  //   実生徒データを表示せず、session token も触らない (401→clearSession による session 破壊を防止)。
  //   既存の throw 失敗パスに合流し、各 widget の try/catch が空表示で耐える。
  if (typeof window.ajPreviewMode === 'function' && window.ajPreviewMode()) {
    const e = new Error('プレビュー表示中のためデータは取得しません'); e.status = 0; e.preview = true; throw e;
  }
  const token = _slToken();
  const headers = Object.assign({'Content-Type': 'application/json'}, options.headers || {});
  if (token) headers['Authorization'] = 'Bearer ' + token;
  const res = await fetch(SL_API_BASE + path, Object.assign({}, options, { headers }));
  if (!res.ok) {
    let detailRaw = '';
    try { const j = await res.json(); detailRaw = j.detail; } catch {}
    if (res.status === 401 && window.AuthGuard) {
      // session expired
      try { window.AuthGuard.clearSession && window.AuthGuard.clearSession(); } catch {}
    }
    const msg = _slFormatErrDetail(detailRaw) || `HTTP ${res.status}`;
    const err = new Error(msg);
    err.status = res.status;
    err.detail = detailRaw;
    throw err;
  }
  return res.json();
}

function initStudyLog() {
  // 🚨 2026-05-13 塾長指示「絶対に消えない」: section の display は **絶対に none にしない**。
  // - eligible: 元の HTML (chart/history/form) をそのまま表示
  // - ineligible: innerHTML を upgrade banner に置換
  // - auth pending: 元の HTML のまま表示 (空 chart は loadMyStudyLogs で埋まる)
  // - auth fail (10 retry 後も student 不明): 元の HTML のまま + 上部に notice 表示
  const section = document.querySelector('.study-log-section');
  if (!section) return;
  // 絶対に display:none にしない (常に visible)
  section.style.display = '';

  // 元の HTML を保存 (eligible 状態で復元可能にする)
  if (!section._originalHTML) {
    section._originalHTML = section.innerHTML;
  }

  const renderUpgradeBanner = () => {
    section.innerHTML = `
      <div class="section-title"><h2>📚 学習記録 <span style="font-size:0.65em;background:linear-gradient(135deg,#fbbf24,#ec4899);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-weight:800;">プレミアム限定</span></h2></div>
      <div style="padding:1.2rem; background:rgba(251,191,36,0.06); border:1px dashed rgba(251,191,36,0.35); border-radius:12px; text-align:center;">
        <div style="font-size:2.5rem; margin-bottom:0.5rem;">🎯</div>
        <div style="color:#fbbf24; font-weight:700; font-size:1.05rem; margin-bottom:0.5rem;">プレミアム以上で利用可</div>
        <p style="color:#a1a1aa; font-size:0.88rem; margin:0.5rem 0 1rem 0;">毎日の学習時間・教材・科目を記録し、AI が学習進捗を分析。プレミアムプラン以上で利用可能です。</p>
        <button type="button" class="course-inquiry-btn" data-course="kokuritsu_nankan" data-source="study-log" style="display:inline-block; padding:0.85rem 1.5rem; background:linear-gradient(135deg,#fbbf24,#ec4899); color:#fff; border:0; border-radius:10px; font-weight:700; font-size:0.95rem; cursor:pointer; box-shadow:0 4px 12px rgba(236,72,153,0.3);">⭐ プレミアムにアップグレード</button>
        <div class="course-inquiry-msg" style="margin-top:0.7rem; font-size:0.82rem;"></div>
      </div>`;
    bindCourseInquiryButtons(section);
  };

  // auth pending → 元の HTML 表示・bind は skip (再試行で bind する)
  // auth fail → 元の HTML 表示 + 上部に notice
  const showAuthRetryNotice = () => {
    // 既存 HTML の上部に notice を挿入
    const notice = document.createElement('div');
    notice.id = 'studyLogAuthNotice';
    notice.style.cssText = 'padding:0.7rem 1rem; background:rgba(245,158,11,0.10); border:1px solid rgba(245,158,11,0.35); border-radius:10px; margin-bottom:1rem; font-size:0.85rem; color:#fbbf24; display:flex; align-items:center; gap:0.5rem; flex-wrap:wrap;';
    notice.innerHTML = `
      <span>⚠️ 認証情報の取得に時間がかかっています。表示が崩れている場合は再読込してください。</span>
      <button type="button" onclick="window.location.reload()" style="padding:0.35rem 0.8rem; background:rgba(245,158,11,0.2); border:1px solid rgba(245,158,11,0.5); border-radius:6px; color:#fbbf24; font-weight:700; cursor:pointer; font-size:0.8rem;">🔄 再読込</button>
    `;
    // section の先頭に挿入 (既に挿入済ならスキップ)
    if (!document.getElementById('studyLogAuthNotice')) {
      section.insertBefore(notice, section.firstChild);
    }
  };

  const bindStudyLogForm = () => {
    const dateInput = document.getElementById('slDate');
    if (dateInput) dateInput.value = _slJstDate(0);
    const btn = document.getElementById('slSubmitBtn');
    if (btn && !btn._slBound) {
      btn.addEventListener('click', submitStudyLog);
      btn._slBound = true;
    }
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
  };

  const tryInit = (retries) => {
    const student = (window.AuthGuard && window.AuthGuard.getStudent && window.AuthGuard.getStudent()) || null;
    if (!student) {
      if (retries > 0) {
        setTimeout(() => tryInit(retries - 1), 200);
      } else {
        // 認証情報取得失敗: 元 HTML のまま + notice 表示 (絶対に hide しない)
        showAuthRetryNotice();
      }
      return;
    }
    // course フィールドが未取得 (auth refresh 待ち) の場合は polling 継続
    if (typeof student.course === 'undefined' && retries > 0) {
      setTimeout(() => tryInit(retries - 1), 200);
      return;
    }
    // 新プラン体系 2026-05-06: 国公立難関本クラス OR プレミアム以上で学習管理機能を解放
    const isTarget = _canUseStudyMgmt(student);
    if (!isTarget) {
      // 一般生徒には機能の存在告知 + 申込導線 (機会損失防止)
      renderUpgradeBanner();
      return;
    }
    // Eligible: 元の HTML がそのまま表示されているはず・form を bind して logs ロード
    bindStudyLogForm();
    loadMyStudyLogs();
  };
  tryInit(10);
}

// ==========================================================================
// 📝 学習記録 クイック CTA (上部配置・engagement 改善 2026-05-11)
// 入力フォームが下部 9 section 下に埋もれていた問題への対処。
// 国公立難関大学コース or プレミアム以上で表示・1-tap quick log + 詳細フォーム導線
// ==========================================================================
function initStudyLogQuickCta() {
  const section = document.querySelector('.study-log-quick-cta');
  if (!section) return;
  // 🚨 2026-05-13 塾長指示「絶対に消えない」: section の display は **絶対に none にしない**。
  // - eligible: 「今日の学習を記録しよう」+ 1-tap buttons
  // - ineligible: 「📚 学習記録 (プレミアム限定)」案内 + アップグレード導線
  // - auth pending: eligible の見た目で polling (button 押下は loadMyStudyLogs 内 auth check で弾く)
  // - auth fail: eligible の見た目でそのまま (再読込導線は study-log-section に表示)
  section.style.display = '';

  // 元の HTML を保存 (ineligible → eligible に変化した時の復元用)
  if (!section._originalHTML) {
    section._originalHTML = section.innerHTML;
  }

  // ineligible 用: 「プレミアム限定」アップグレード CTA に置換
  const renderUpgradeCta = () => {
    section.style.background = 'linear-gradient(135deg, rgba(251,191,36,0.12), rgba(236,72,153,0.10))';
    section.style.borderColor = 'rgba(251,191,36,0.4)';
    section.innerHTML = `
      <div style="display:flex; align-items:center; justify-content:space-between; gap:0.9rem; flex-wrap:wrap;">
        <div style="flex:1 1 220px; min-width:200px;">
          <div style="display:inline-block; padding:0.18rem 0.65rem; background: linear-gradient(135deg,#fbbf24,#ec4899); border-radius:999px; font-size:0.7rem; font-weight:800; color:#fff; margin-bottom:0.4rem; letter-spacing:0.02em;">⭐ プレミアム限定</div>
          <h3 style="margin:0 0 0.25rem 0; font-size:1.1rem; color:#fff; font-weight:800; line-height:1.35;">📚 学習記録で日々の頑張りを可視化</h3>
          <p style="margin:0; font-size:0.82rem; color:#fef3c7; line-height:1.5;">毎日の学習時間・教材を記録 → 30 日グラフと履歴で振り返り。プレミアム以上で開放。</p>
        </div>
        <div style="display:flex; gap:0.45rem; flex-wrap:wrap; align-items:center;">
          <button type="button" class="course-inquiry-btn" data-course="kokuritsu_nankan" data-source="study-log-quick" style="padding:0.6rem 1.1rem; background: linear-gradient(135deg,#fbbf24,#ec4899); border:0; border-radius:10px; color:#fff; font-weight:800; font-size:0.88rem; cursor:pointer; min-height:44px; box-shadow:0 4px 12px rgba(236,72,153,0.3);">⭐ アップグレード →</button>
        </div>
      </div>
      <div class="course-inquiry-msg" style="margin-top:0.55rem; font-size:0.82rem;"></div>
    `;
    bindCourseInquiryButtons(section);
  };

  const tryShow = (retries) => {
    const student = (window.AuthGuard && window.AuthGuard.getStudent && window.AuthGuard.getStudent()) || null;
    if (!student) {
      if (retries > 0) setTimeout(() => tryShow(retries - 1), 200);
      // 認証取得失敗時も section は visible のまま (元 HTML 表示・button は loadMyStudyLogs 等で弾かれる)
      return;
    }
    // course フィールドが auth refresh 待ちの場合は polling 継続
    if (typeof student.course === 'undefined' && retries > 0) {
      setTimeout(() => tryShow(retries - 1), 200);
      return;
    }
    // 学習管理機能と同じ判定 (kokuritsu_nankan / premium / family / founder_special / student_addon)
    if (!_canUseStudyMgmt(student)) {
      renderUpgradeCta();
      return;
    }

    // 今日の学習時間を表示 + #todayMinutes (上部 stats) も real data に上書き
    refreshSlQuickCtaToday();

    // 🚨 streak 途切れ banner: 3 日以上未記録の active 生徒に表示 (塾長指示 2026-05-19)
    _slStreakBannerCheck();
    _slBindStreakDismiss();

    // 「詳しく記録」 → study-log section へ smooth scroll + 分入力欄 focus
    const detailBtn = document.getElementById('slqcDetailBtn');
    if (detailBtn && !detailBtn._slBound) {
      detailBtn.addEventListener('click', () => {
        const target = document.querySelector('.study-log-section');
        if (!target) return;
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        // scroll 完了を待ってから minutes 欄に focus (UX: 開いてすぐ入力できる)
        setTimeout(() => {
          const min = document.getElementById('slMinutes');
          if (min && typeof min.focus === 'function') {
            try { min.focus({ preventScroll: true }); } catch (_) { min.focus(); }
          }
        }, 600);
        try { window.track && window.track('sl_quick_cta_detail_open'); } catch (_) {}
      });
      detailBtn._slBound = true;
    }

    // 1-tap quick log buttons
    section.querySelectorAll('.slqc-quick-btn').forEach(btn => {
      if (btn._slBound) return;
      btn.addEventListener('click', () => {
        const m = parseInt(btn.dataset.min, 10);
        if (!Number.isFinite(m) || m < 1) return;
        quickLogMinutes(m, btn);
      });
      btn._slBound = true;
    });
  };
  tryShow(10);
}

// 今日の学習時間を /api/study-logs/me から取得して CTA + 上部 #todayMinutes を更新
// 🛡️ retry button cleanup helper (2026-05-19 audit re-review): orphan setInterval 防止
// 任意 path から msgEl の retry timer を解除 (success cleanup / 連続失敗 path で必須)
function _slClearRetryTimer(msgEl) {
  if (!msgEl) return;
  if (msgEl._slRetryTimer) {
    clearInterval(msgEl._slRetryTimer);
    msgEl._slRetryTimer = null;
  }
  msgEl.onkeydown = null;
}

// 🛡️ retry button helper (2026-05-19): iPhone Safari でも「タップ可能」が伝わるよう
// underline + 背景色 + padding + border-radius で物理ボタン化。429/5xx は countdown 付き disable で連打防止。
// audit re-review fix:
//   - msgEl._slRetryTimer に保存 → 連続呼出で前回 clearInterval (orphan 防止)
//   - 内部 span#_slRetryInner の textContent だけ毎秒更新 (innerHTML 全書換 reflow 回避)
//   - keydown (Enter/Space) で click 発火 (accessibility)
function _slMakeRetryButton(msgEl, label, opts) {
  if (!msgEl) return;
  _slClearRetryTimer(msgEl);
  opts = opts || {};
  const countdown = Math.max(0, Number(opts.countdown || 0));
  const color = opts.color || '#fbbf24';
  const bg = opts.bg || 'rgba(251,191,36,0.15)';
  msgEl.style.color = color;
  msgEl.setAttribute('role', 'button');
  msgEl.setAttribute('tabindex', '0');
  // span 構造を 1 度だけ生成 (毎秒 reflow を避ける)
  msgEl.innerHTML = '<span id="_slRetryInner" style="display:inline-block; padding:6px 12px; background:' + bg + '; border-radius:6px; text-decoration:underline; cursor:pointer;"></span>';
  const inner = msgEl.querySelector('#_slRetryInner');
  if (!inner) return;
  const setText = (sec) => {
    inner.textContent = (sec > 0) ? (label + ' (' + sec + '秒)') : label;
  };
  const enable = () => {
    msgEl.style.pointerEvents = '';
    msgEl.style.opacity = '';
    setText(0);
    msgEl.onclick = () => {
      _slClearRetryTimer(msgEl);
      msgEl.textContent = '読込中...';
      window._slqcInflight = false;
      refreshSlQuickCtaToday();
    };
    msgEl.onkeydown = (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        if (typeof msgEl.onclick === 'function') msgEl.onclick();
      }
    };
  };
  let remaining = countdown;
  if (remaining > 0) {
    msgEl.style.pointerEvents = 'none';
    msgEl.style.opacity = '0.7';
    msgEl.onclick = null;
    msgEl.onkeydown = null;
    setText(remaining);
    msgEl._slRetryTimer = setInterval(() => {
      remaining -= 1;
      if (remaining <= 0) {
        _slClearRetryTimer(msgEl);
        enable();
      } else {
        setText(remaining);
      }
    }, 1000);
  } else {
    enable();
  }
}

// 🚨 streak 途切れ warning banner check (塾長指示 2026-05-19): 「使ってるが記録ゼロ」85% 現象対応
// 表示条件: 3 日以上連続で記録なし AND 過去 14 日に 1 件以上の記録あり (= かつて記録した経験あり)
// 非表示条件: ①今日記録あり ②今日 dismiss 済 ③新規生徒 (記録 0 件)
// ポジティブ訴求 (「今日記録すると streak 再スタート」) で罪悪感誘導は避ける
async function _slStreakBannerCheck() {
  const banner = document.getElementById('slStreakWarning');
  const daysEl = document.getElementById('slStreakDays');
  if (!banner || !daysEl) return;
  try {
    // 今日 dismiss 済か (localStorage)
    const dismissKey = 'ai_juku_streak_warning_dismissed';
    const dismissedDate = (function() {
      try { return localStorage.getItem(dismissKey) || ''; } catch (_) { return ''; }
    })();
    const today = _slJstDate(0);
    if (dismissedDate === today) {
      banner.style.display = 'none';
      return;
    }
    // 過去 14 日の学習記録を取得
    const data = await slApiFetch('/api/study-logs/me?days=14&limit=200');
    const daily = (data && data.daily) || [];
    if (daily.length === 0) {
      // 新規生徒 (記録 0 件) → 表示しない
      banner.style.display = 'none';
      return;
    }
    // 日付別に min を合計 (JST date string)
    const dayMap = {};
    daily.forEach(function(d) {
      if (!d || !d.date) return;
      const k = String(d.date).slice(0, 10);
      dayMap[k] = (dayMap[k] || 0) + (d.minutes || 0);
    });
    // 過去 14 日で記録があった日が 1 つもないなら「実質新規」扱いで非表示
    const recordedDays = Object.keys(dayMap).filter(function(k) { return dayMap[k] > 0; });
    if (recordedDays.length === 0) {
      banner.style.display = 'none';
      return;
    }
    // 今日 (JST) を起点に連続未記録日数を計算
    let streakBroken = 0;
    for (let i = 0; i < 14; i++) {
      const d = _slJstDate(i);
      if ((dayMap[d] || 0) > 0) break;
      streakBroken += 1;
    }
    if (streakBroken >= 3) {
      daysEl.textContent = String(streakBroken);
      banner.style.display = 'block';
    } else {
      banner.style.display = 'none';
    }
  } catch (e) {
    // 失敗時は banner 表示せず (silent skip OK · 既存 CTA で代替可能)
    console.warn('[Streak] banner check failed:', e && e.message);
    banner.style.display = 'none';
  }
}

// 🚨 streak 途切れ banner dismiss button handler (今日中は閉じる)
function _slBindStreakDismiss() {
  const btn = document.getElementById('slStreakDismiss');
  const banner = document.getElementById('slStreakWarning');
  if (!btn || !banner || btn._slStreakBound) return;
  btn._slStreakBound = true;
  btn.addEventListener('click', function() {
    try {
      localStorage.setItem('ai_juku_streak_warning_dismissed', _slJstDate(0));
    } catch (_) {}
    banner.style.display = 'none';
  });
}

async function refreshSlQuickCtaToday() {
  // 🛡️ race condition guard (audit #7 / 2026-05-19): concurrent 呼出で
  // 「成功してるのに retry CTA 残留」を防ぐ。in-flight 中は即 return。
  if (window._slqcInflight) return;
  window._slqcInflight = true;
  const titleEl = document.getElementById('slqcTitle');
  const subEl = document.getElementById('slqcSub');
  const badgeEl = document.getElementById('slqcBadge');
  const todayStatEl = document.getElementById('todayMinutes');
  const msgEl = document.getElementById('slqcMessage');
  let todayMin = 0;
  // 🛡️ try/finally で inflight guard を保証 (regression audit #6 / 2026-05-19):
  // unhandled exception path でも _slqcInflight=false にして tab 切替後 stuck を防止
  try {
    try {
      // days=2 にして 0 件でも空配列が返る (days=0 は backend バリデーションで拒否)
      const data = await slApiFetch('/api/study-logs/me?days=2&limit=20');
      const today = _slJstDate(0);
      (data.daily || []).forEach(d => {
        if (d && String(d.date).slice(0, 10) === today) todayMin += (d.minutes || 0);
      });
    } catch (e) {
      console.warn('[StudyLog] today refresh failed:', e && e.message, 'status=', e && e.status);
      // 🛡️ silent fail 修正 (塾長指示 2026-05-19): API 失敗を生徒に可視化
      // audit #5 fix: status code 優先で判定 (regex on message は脆弱 / 403/429/500 取りこぼし防止)
      if (msgEl) {
        const status = (e && typeof e.status === 'number') ? e.status : 0;
        const errStr = (e && e.message) || '';
        const isAuth = (status === 401) || /401|unauthorized|expired/i.test(errStr);
        const isPerm = (status === 403);
        const isRate = (status === 429);
        const isServer = (status >= 500 && status < 600);
        // audit re-review: orphan timer 防止と a11y state clean
        _slClearRetryTimer(msgEl);
        msgEl.removeAttribute('role');
        msgEl.removeAttribute('tabindex');
        msgEl.style.pointerEvents = '';
        msgEl.style.opacity = '';
        if (isAuth) {
          msgEl.innerHTML = '⚠️ ログイン状態が切れたようです — <a href="login.html" style="display:inline-block; padding:6px 12px; background:rgba(125,211,252,0.15); border-radius:6px; color:#7dd3fc; text-decoration:underline;">再ログイン</a>';
          msgEl.style.color = '#fca5a5';
          msgEl.style.cursor = '';
          msgEl.onclick = null;
        } else if (isPerm) {
          msgEl.innerHTML = '⚠️ アクセス権がありません — <a href="mailto:info@trillion-ai-juku.com" style="display:inline-block; padding:6px 12px; background:rgba(252,165,165,0.15); border-radius:6px; color:#fca5a5; text-decoration:underline;">塾長にメール</a>';
          msgEl.style.color = '#fca5a5';
          msgEl.style.cursor = '';
          msgEl.onclick = null;
        } else if (isRate) {
          // 429: 30 秒 countdown 付き disable で連打防止 (UX 致命 #2 fix / サーバ保護も兼ねる)
          _slMakeRetryButton(msgEl, '⚠️ アクセスが集中しています — 待ってから再試行', { countdown: 30 });
        } else if (isServer) {
          // 5xx: 10 秒 countdown で過剰連打防止 (中学生でも分かる言葉に変換)
          _slMakeRetryButton(msgEl, '⚠️ いまサーバーで問題が発生しました — タップで再試行', { countdown: 10 });
        } else {
          _slMakeRetryButton(msgEl, '⚠️ 学習記録の読込に失敗 — タップで再試行', { countdown: 0 });
        }
      }
      return;
    }
    // 上部 stats #todayMinutes を実データで上書き (これまで demo の 45 が固定表示されていた)
    if (todayStatEl) todayStatEl.textContent = String(todayMin);
    // 🛡️ silent fail fix (2026-05-19): retry 成功時の状態 cleanup (前回エラー残留防止)
    if (msgEl) {
      // audit re-review: setInterval orphan 防止 (success path で必ず clearInterval)
      _slClearRetryTimer(msgEl);
      msgEl.onclick = null;
      msgEl.style.cursor = '';
      msgEl.style.color = '#a78bfa';
      msgEl.style.pointerEvents = '';
      msgEl.style.opacity = '';
      msgEl.removeAttribute('role');
      msgEl.removeAttribute('tabindex');
      // ⚠️ アイコン残留判定 — innerHTML/textContent 両方を check (link 含む 401 ケース対応)
      const txt = (msgEl.textContent || '');
      if (txt.includes('⚠️') || txt === '読込中...') {
        msgEl.innerHTML = '';
      }
    }
    if (todayMin > 0) {
      if (badgeEl) badgeEl.textContent = '⚡ 今日 進行中';
      if (titleEl) titleEl.textContent = `今日 ${todayMin} 分 学習中`;
      if (subEl) subEl.textContent = '追加で記録すれば塾長への報告も自動。1日の合計が積み上がります。';
    } else {
      if (badgeEl) badgeEl.textContent = '📝 今日の学習';
      if (titleEl) titleEl.textContent = '今日の学習を記録しよう';
      if (subEl) subEl.textContent = '塾長があなたの頑張りを見て、いいねやコメントを送ります。';
    }
  } finally {
    // 🛡️ inflight guard release (audit #7 + regression #6 / 2026-05-19):
    // 全 path (success / catch / unhandled exception) で必ず解除して stuck を防止
    window._slqcInflight = false;
  }
}

// 1-tap で minutes だけ送信。subject は直近の log から推定。
// 直近の記録が無い場合は誤った subject が混入しないよう、詳細フォームに誘導 (kokuritsu_nankan は複数科目)
async function quickLogMinutes(minutes, btn) {
  if (!minutes || minutes < 1) return;
  const msg = document.getElementById('slqcMessage');
  // audit re-review: retry button 中の orphan timer 防止 (msg を上書きする前に clearInterval)
  _slClearRetryTimer(msg);
  // 直近 14 日の最新 log から subject を推定。なければ「詳しく記録」に誘導 (UX review: 英語デフォは複数科目生徒で誤分類リスク)
  let subject = null;
  try {
    const recent = await slApiFetch('/api/study-logs/me?days=14&limit=10');
    const logs = recent && recent.logs ? recent.logs : [];
    if (logs.length > 0 && logs[0].subject) subject = logs[0].subject;
  } catch (e) {
    // recent fetch 失敗時はネットワークエラー扱いで一旦中断
    if (msg) { msg.textContent = '⚠️ ネットワークエラー。少し待って再試行してください'; msg.style.color = '#fca5a5'; }
    return;
  }
  if (!subject) {
    // 初回 (履歴なし) → 詳細フォームへ誘導して科目選択を促す
    if (msg) {
      msg.style.color = '#fbbf24';
      msg.innerHTML = '📚 まずは科目を選んで1件目を記録しよう → <a href="#" id="slqcGoDetail" style="color:#a78bfa; text-decoration:underline;">詳しい記録を開く</a>';
      const goDetail = document.getElementById('slqcGoDetail');
      if (goDetail) {
        goDetail.addEventListener('click', (ev) => {
          ev.preventDefault();
          const target = document.querySelector('.study-log-section');
          if (target) {
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            setTimeout(() => {
              const minEl = document.getElementById('slMinutes');
              if (minEl) minEl.value = String(minutes);
              const subjEl = document.getElementById('slSubject');
              if (subjEl && typeof subjEl.focus === 'function') {
                try { subjEl.focus({ preventScroll: true }); } catch (_) { subjEl.focus(); }
              }
            }, 600);
          }
        }, { once: true });
      }
    }
    return;
  }
  // confirm でユーザに最終確認 (誤クリックで意図しない記録が残るのを防止)
  // iOS Safari 互換のため \n\n は使わず 1 行ずつシンプルに
  const ok = window.confirm(`今日「${subject}」を ${minutes} 分 記録しますか?\n(教材名・メモは「詳しく記録」から後で追加できます)`);
  if (!ok) return;

  if (msg) { msg.textContent = '保存中...'; msg.style.color = '#a78bfa'; }
  if (btn) btn.disabled = true;
  // 同時押し対策: 全 quick btn を一時 disable
  const allBtns = document.querySelectorAll('.slqc-quick-btn');
  allBtns.forEach(b => b.disabled = true);

  try {
    const resp = await slApiFetch('/api/study-logs', {
      method: 'POST',
      body: JSON.stringify({ subject, minutes }),
    });
    const newId = resp && resp.id;
    // ✅ 成功メッセージ + 取り消しリンク (誤タップ救済)
    if (msg) {
      msg.style.color = '#86efac';
      const baseText = `✅ ${subject} ${minutes}分 を記録しました`;
      if (newId) {
        msg.innerHTML = `${baseText} <a href="#" id="slqcUndo" data-id="${newId}" style="color:#fca5a5; text-decoration:underline; margin-left:0.5rem;">取り消す</a>`;
        const undoLink = document.getElementById('slqcUndo');
        if (undoLink) undoLink.addEventListener('click', (ev) => { ev.preventDefault(); undoQuickLog(newId); }, { once: true });
      } else {
        msg.textContent = baseText;
      }
    }
    try { window.track && window.track('sl_quick_log', { minutes, subject }); } catch (_) {}
    // CTA 上部表示・stats・詳細セクション全部 refresh
    await refreshSlQuickCtaToday();
    // streak banner 再計算 (今日記録したので消えるはず)
    _slStreakBannerCheck();
    if (typeof loadMyStudyLogs === 'function') {
      try { await loadMyStudyLogs(); } catch (_) {}
    }
  } catch (e) {
    const detail = (e && e.message) || '保存失敗';
    if (msg) { msg.textContent = '❌ ' + detail; msg.style.color = '#fca5a5'; }
  } finally {
    allBtns.forEach(b => b.disabled = false);
  }
}

// 誤タップ救済: クイックログ直後の取り消し
async function undoQuickLog(logId) {
  const msg = document.getElementById('slqcMessage');
  if (!logId) return;
  // audit re-review: retry button 中の orphan timer 防止
  _slClearRetryTimer(msg);
  if (msg) { msg.textContent = '取り消し中...'; msg.style.color = '#a78bfa'; }
  try {
    await slApiFetch('/api/study-logs/' + encodeURIComponent(logId), { method: 'DELETE' });
    if (msg) { msg.textContent = '🗑️ 取り消しました'; msg.style.color = '#a1a1aa'; }
    await refreshSlQuickCtaToday();
    // streak banner 再計算 (取り消しで今日 0 分に戻った場合の表示判定)
    _slStreakBannerCheck();
    if (typeof loadMyStudyLogs === 'function') {
      try { await loadMyStudyLogs(); } catch (_) {}
    }
  } catch (e) {
    if (msg) { msg.textContent = '❌ 取り消し失敗: ' + ((e && e.message) || ''); msg.style.color = '#fca5a5'; }
  }
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

// PDF → Claude Vision 用 image parts 配列。pdf.js でページを canvas に描画 → JPEG 化
async function _pdfToImageParts(file, opts) {
  const { maxPages = 3, scale = 2.0, quality = 0.82, maxSide = 1400 } = opts || {};
  if (file.size > 10_000_000) {
    throw new Error(`ファイルサイズが大きすぎます (${(file.size / 1_000_000).toFixed(1)}MB)。10MB以下の PDF をご利用ください`);
  }
  if (typeof pdfjsLib === 'undefined') throw new Error('PDF ライブラリの読込に失敗しました (ページを再読込してください)');
  if (!pdfjsLib.GlobalWorkerOptions.workerSrc) {
    pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
  }
  const arrayBuffer = await file.arrayBuffer();
  let pdf;
  try {
    pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
  } catch (err) {
    const m = (err && err.message) || '';
    if (/password|encrypt/i.test(m) || (err && err.name === 'PasswordException')) {
      throw new Error('PDF がパスワード保護されています。保護を解除してから再アップロードしてください');
    }
    if (/Invalid PDF|InvalidPDF/i.test(m)) {
      throw new Error('PDF が破損しているか、有効な PDF ではありません');
    }
    throw err;
  }
  const totalPages = Math.min(pdf.numPages, maxPages);
  const parts = [];
  for (let p = 1; p <= totalPages; p++) {
    const page = await pdf.getPage(p);
    let viewport = page.getViewport({ scale });
    // long edge を maxSide に合わせる (ペイロード抑制)
    const longSide = Math.max(viewport.width, viewport.height);
    if (longSide > maxSide) {
      const adjustedScale = scale * (maxSide / longSide);
      viewport = page.getViewport({ scale: adjustedScale });
    }
    const canvas = document.createElement('canvas');
    canvas.width = Math.ceil(viewport.width);
    canvas.height = Math.ceil(viewport.height);
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#fff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    await page.render({ canvasContext: ctx, viewport }).promise;
    const dataUrl = canvas.toDataURL('image/jpeg', quality);
    const base64 = dataUrl.split(',')[1];
    parts.push({ type: 'image', source: { type: 'base64', media_type: 'image/jpeg', data: base64 } });
  }
  if (!parts.length) throw new Error('PDF にページがありません');
  return parts;
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
  // 🚨 2026-05-13: chart / list の skeleton を hide (loadMyStudyLogs が走ったら本物データへ遷移)
  const chartSkel = document.getElementById('slDailyChartSkeleton');
  if (chartSkel) chartSkel.style.display = 'none';
  const listSkel = document.getElementById('slLogListSkeleton');
  if (listSkel) listSkel.style.display = 'none';
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
  // 🚨 2026-05-13 塾長指示「絶対に消えない」: section の display は **絶対に none にしない**。
  const section = document.querySelector('.study-plan-section');
  if (section) section.style.display = '';  // 初期から表示
  const tryInit = (retries) => {
    const student = (window.AuthGuard && window.AuthGuard.getStudent && window.AuthGuard.getStudent()) || null;
    if (!student) {
      // ⚠️ auth pending: hide しない (元 HTML のまま polling 継続)
      if (retries > 0) setTimeout(() => tryInit(retries - 1), 200);
      return;
    }
    if (typeof student.course === 'undefined' && retries > 0) {
      setTimeout(() => tryInit(retries - 1), 200);
      return;
    }
    if (!_canUseStudyMgmt(student)) {
      // 一般生徒 (通塾生プラン等) には CTA 表示 (Frontend m-1: 機会損失防止)
      if (section) {
        section.style.display = '';
        section.innerHTML = `
          <div class="section-title"><h2>📅 学習計画 <span style="font-size:0.65em;background:linear-gradient(135deg,#fbbf24,#ec4899);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-weight:800;">プレミアム限定</span></h2></div>
          <div style="padding:1.2rem; background:rgba(251,191,36,0.06); border:1px dashed rgba(251,191,36,0.35); border-radius:12px; text-align:center;">
            <div style="font-size:2.5rem; margin-bottom:0.5rem;">📅</div>
            <div style="color:#fbbf24; font-weight:700; font-size:1.05rem; margin-bottom:0.5rem;">志望校合格までのロードマップを描こう</div>
            <p style="color:#a1a1aa; font-size:0.88rem; margin:0.5rem 0 1rem 0;">学習計画 + 進捗ガントチャート + 月間カレンダーで「いつまでに何を」を可視化。</p>
            <button type="button" class="course-inquiry-btn" data-course="kokuritsu_nankan" data-source="study-plan" style="display:inline-block; padding:0.85rem 1.5rem; background:linear-gradient(135deg,#fbbf24,#ec4899); color:#fff; border:0; border-radius:10px; font-weight:700; font-size:0.95rem; cursor:pointer; box-shadow:0 4px 12px rgba(236,72,153,0.3);">⭐ プレミアムにアップグレード</button>
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
    // 📅 隔日学習計画 (2026-05-22 塾長指示): preset ボタン + checkbox の event bind
    _bindWeekPatternUI();
    // AI 機能 (A+B+C)
    bindStudyPlanAiButtons();
    loadMyStudyPlans();
    // 📚 マイ参考書 (塾長指示 2026-05-14): 学習計画タブ内 + カリキュラム生成画面 両方 init
    initMyMaterials('mm');
    initMyMaterials('cum');
    loadMyMaterials();  // 1 fetch で両 list ([data-mm-list]) 同時更新
  };
  tryInit(10);
}

// ==========================================================================
// 📚 マイ参考書/問題集 (塾長指示 2026-05-14)
// 生徒が自分で使っている参考書を登録 → カリキュラム AI 生成時に継続使用前提で組み込み
// ==========================================================================
const MM_SUBJECTS = [
  '英語', '数学', '国語', '現代文', '古文', '漢文',
  '理科', '物理', '化学', '生物', '地学',
  '社会', '日本史', '世界史', '地理', '倫理', '政経',
  '情報', '小論文', '面接対策', 'その他',
];
const MM_STATUS_LABEL = {using: '📖 使用中', completed: '✅ 完了', paused: '⏸ お休み中'};
const MM_STATUS_COLOR = {using: '#22d3ee', completed: '#34d399', paused: '#a1a1aa'};

// 🔧 2026-05-14 塾長指示「カリキュラムの欄にも入れる」: prefix で複数 UI 対応
// - prefix 'mm' = 学習計画タブ内 (mmList, mmName, mmSubject, mmStatus, mmNote, mmFormWrap, etc.)
// - prefix 'cum' = カリキュラム生成 AI フォーム内 (cumList, cumName, ...)
// 両 UI 同時動作: 一方で追加/削除/状態変更すると、loadMyMaterials() が両 [data-mm-list] を同時更新
function initMyMaterials(prefix) {
  prefix = prefix || 'mm';
  // populate subject dropdown
  const subjSel = document.getElementById(`${prefix}Subject`);
  if (subjSel && !subjSel.options.length) {
    MM_SUBJECTS.forEach(s => {
      const o = document.createElement('option');
      o.value = s; o.textContent = s;
      subjSel.appendChild(o);
    });
  }
  // toggle form
  const toggleBtn = document.getElementById(`${prefix}ToggleFormBtn`);
  const wrap = document.getElementById(`${prefix}FormWrap`);
  if (toggleBtn && !toggleBtn._mmBound) {
    toggleBtn.addEventListener('click', () => {
      if (!wrap) return;
      wrap.style.display = wrap.style.display === 'none' ? '' : 'none';
      if (wrap.style.display !== 'none') {
        const nameEl = document.getElementById(`${prefix}Name`);
        if (nameEl) nameEl.focus();
      }
    });
    toggleBtn._mmBound = true;
  }
  const cancelBtn = document.getElementById(`${prefix}CancelBtn`);
  if (cancelBtn && !cancelBtn._mmBound) {
    cancelBtn.addEventListener('click', () => {
      if (wrap) wrap.style.display = 'none';
      clearMmForm(prefix);
    });
    cancelBtn._mmBound = true;
  }
  const saveBtn = document.getElementById(`${prefix}SaveBtn`);
  if (saveBtn && !saveBtn._mmBound) {
    saveBtn.addEventListener('click', () => submitMyMaterial(prefix));
    saveBtn._mmBound = true;
  }
}

function clearMmForm(prefix) {
  prefix = prefix || 'mm';
  const name = document.getElementById(`${prefix}Name`);
  const note = document.getElementById(`${prefix}Note`);
  const status = document.getElementById(`${prefix}Status`);
  const msg = document.getElementById(`${prefix}FormMsg`);
  if (name) name.value = '';
  if (note) note.value = '';
  if (status) status.value = 'using';
  if (msg) msg.textContent = '';
}

async function submitMyMaterial(prefix) {
  prefix = prefix || 'mm';
  const name = (document.getElementById(`${prefix}Name`).value || '').trim();
  const subject = document.getElementById(`${prefix}Subject`).value;
  const status = document.getElementById(`${prefix}Status`).value;
  const note = (document.getElementById(`${prefix}Note`).value || '').trim() || null;
  const msg = document.getElementById(`${prefix}FormMsg`);
  const saveBtn = document.getElementById(`${prefix}SaveBtn`);
  if (!name) {
    if (msg) { msg.style.color = '#fca5a5'; msg.textContent = '⚠️ 参考書名を入力してください'; }
    return;
  }
  if (!subject) {
    if (msg) { msg.style.color = '#fca5a5'; msg.textContent = '⚠️ 科目を選択してください'; }
    return;
  }
  saveBtn.disabled = true; saveBtn.textContent = '登録中...';
  try {
    await slApiFetch('/api/student/materials', {
      method: 'POST',
      body: JSON.stringify({name, subject, status, note}),
    });
    if (msg) { msg.style.color = '#86efac'; msg.textContent = '✅ 登録しました'; }
    clearMmForm(prefix);
    const wrap = document.getElementById(`${prefix}FormWrap`);
    if (wrap) wrap.style.display = 'none';
    await loadMyMaterials();
  } catch (e) {
    if (msg) { msg.style.color = '#fca5a5'; msg.textContent = '❌ ' + (e.message || '登録失敗'); }
  } finally {
    saveBtn.disabled = false; saveBtn.textContent = '💾 登録';
  }
}

function _renderMmListInto(list, materials) {
  if (!materials.length) {
    list.innerHTML = '<div style="color:#71717a; font-size:0.78rem; padding:0.5rem;">📚 まだ登録された参考書がありません。「＋追加」から登録すると AI が継続使用前提でカリキュラムを組みます。</div>';
    return;
  }
  list.innerHTML = materials.map(m => {
    const c = MM_STATUS_COLOR[m.status] || '#22d3ee';
    const lab = MM_STATUS_LABEL[m.status] || m.status;
    return `
      <div class="mm-item" data-id="${m.id}" style="background:rgba(0,0,0,0.3); border:1px solid ${c}33; border-radius:8px; padding:0.45rem 0.6rem; display:inline-flex; align-items:center; gap:0.4rem;">
        <span style="color:${c}; font-weight:700; font-size:0.78rem;">${escapeHtml(m.subject)}</span>
        <span style="color:#e4e4e7; font-size:0.82rem;">${escapeHtml(m.name)}</span>
        <span style="color:${c}; font-size:0.7rem;">${lab}</span>
        ${m.note ? `<span style="color:#71717a; font-size:0.7rem;">(${escapeHtml(m.note)})</span>` : ''}
        <button class="mm-cycle-btn" data-id="${m.id}" data-status="${m.status}" aria-label="状態を変更" title="状態を変更 (使用中→完了→お休み→使用中)" style="background:rgba(255,255,255,0.08); border:0; color:#a1a1aa; padding:0.15rem 0.35rem; border-radius:4px; cursor:pointer; font-size:0.7rem;">↻</button>
        <button class="mm-delete-btn" data-id="${m.id}" data-name="${escapeHtml(m.name)}" data-subject="${escapeHtml(m.subject)}" aria-label="削除" title="削除" style="background:rgba(239,68,68,0.15); border:0; color:#fca5a5; padding:0.15rem 0.35rem; border-radius:4px; cursor:pointer; font-size:0.7rem;">✕</button>
      </div>`;
  }).join('');
  list.querySelectorAll('.mm-cycle-btn').forEach(b => b.addEventListener('click', () => cycleMaterialStatus(b.getAttribute('data-id'), b.getAttribute('data-status'), b)));
  list.querySelectorAll('.mm-delete-btn').forEach(b => b.addEventListener('click', () => deleteMyMaterial(b.getAttribute('data-id'), b.getAttribute('data-name'), b.getAttribute('data-subject'))));
}

async function loadMyMaterials() {
  // 全 [data-mm-list] containers (mmList + cumList) を同時更新
  const lists = document.querySelectorAll('[data-mm-list]');
  if (!lists.length) return;
  try {
    const data = await slApiFetch('/api/student/materials/me');
    const materials = data.materials || [];
    lists.forEach(list => _renderMmListInto(list, materials));
  } catch (e) {
    console.error('loadMyMaterials failed:', e);
    lists.forEach(list => {
      list.innerHTML = `<div style="color:#fca5a5; font-size:0.78rem;">⚠️ 読み込み失敗 (${escapeHtml(e.message || '')}) <button onclick="loadMyMaterials()" style="margin-left:0.4rem; background:rgba(99,102,241,0.2); border:0; color:#c7d2fe; padding:0.2rem 0.4rem; border-radius:4px; cursor:pointer; font-size:0.72rem;">再試行</button></div>`;
    });
  }
}

async function cycleMaterialStatus(id, currentStatus, btn) {
  // 連打防止 (★★★ Reviewer 2 #2 対応): ボタン disable + 通信中なら抜ける
  if (btn && btn.disabled) return;
  if (btn) btn.disabled = true;
  const next = currentStatus === 'using' ? 'completed' : (currentStatus === 'completed' ? 'paused' : 'using');
  try {
    await slApiFetch(`/api/student/materials/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      body: JSON.stringify({status: next}),
    });
    await loadMyMaterials();
  } catch (e) {
    alert('状態変更失敗: ' + (e.message || ''));
    // エラー時も真の状態を反映するため refetch
    await loadMyMaterials();
  }
  // 注: loadMyMaterials が DOM を innerHTML で書き換えるので btn は GC される (disabled 解除不要)
}

async function deleteMyMaterial(id, name, subject) {
  // 対象名を明示して誤削除防止 (★★ Reviewer 2 #6 対応)
  const label = name ? `「${name}」(${subject || ''})` : 'この参考書';
  if (!confirm(`${label} を削除しますか?`)) return;
  try {
    await slApiFetch(`/api/student/materials/${encodeURIComponent(id)}`, {method: 'DELETE'});
    await loadMyMaterials();
  } catch (e) {
    alert('削除失敗: ' + (e.message || ''));
  }
}

// inline onclick から呼べるよう global export (memory: feedback_iife_onclick_pitfall.md)
if (typeof window !== 'undefined') {
  window.loadMyMaterials = loadMyMaterials;
  window.cycleMaterialStatus = cycleMaterialStatus;
  window.deleteMyMaterial = deleteMyMaterial;
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
  const aiGenCancel = document.getElementById('spAiGenCancelBtn');
  if (aiGenCancel && !aiGenCancel._spAiBound) {
    aiGenCancel.addEventListener('click', () => { document.getElementById('spAiGenWrap').style.display = 'none'; });
    aiGenCancel._spAiBound = true;
  }
  const aiRecCancel = document.getElementById('spAiRecCancelBtn');
  if (aiRecCancel && !aiRecCancel._spAiBound) {
    aiRecCancel.addEventListener('click', () => { document.getElementById('spAiRecWrap').style.display = 'none'; });
    aiRecCancel._spAiBound = true;
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
      model: 'gemini-2.5-flash',
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
  const jsonStr = txt.replace(/^```(?:json)?\s*|\s*```$/g, '').trim();
  try { return JSON.parse(jsonStr); }
  catch (_e1) {
    // 2026-05-07: 再試行 1: 一番外側の [...]/{...} を抽出
    const m = jsonStr.match(/[\[\{][\s\S]*[\]\}]/);
    if (m) {
      try { return JSON.parse(m[0]); } catch (_e2) {}
    }
    // 2026-05-07: 再試行 2: truncated JSON 救済 (max_tokens で途中切れた場合)
    // 配列なら、最後の "完結した" } の位置までで切り、] を補完
    if (jsonStr.startsWith('[')) {
      // 最後の },\n  { や } } を探す
      const lastCompleteObj = jsonStr.lastIndexOf('},');
      if (lastCompleteObj > 0) {
        const truncated = jsonStr.slice(0, lastCompleteObj + 1) + ']';
        try {
          const arr = JSON.parse(truncated);
          if (Array.isArray(arr) && arr.length > 0) {
            console.warn(`[_spCallAi] truncated 検知 → ${arr.length} 件まで救済`);
            return arr;
          }
        } catch (_e3) {}
      }
    }
    throw new Error('AI 応答の解析に失敗しました。もう一度お試しください。');
  }
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
    // 📚 マイ参考書 (使用中) を取得して AI prompt に注入 (塾長指示 2026-05-14)
    let ownMaterialsSnippet = '';
    try {
      const mm = await slApiFetch('/api/student/materials/me?status=using');
      const mats = (mm && mm.materials) || [];
      if (mats.length) {
        const bySubj = {};
        mats.forEach(m => { (bySubj[m.subject] = bySubj[m.subject] || []).push(m.name); });
        const lines = Object.entries(bySubj).map(([s, names]) => `- ${s}: ${names.slice(0, 8).join(', ')}`);
        ownMaterialsSnippet = `\n\n## 📚 生徒が現在使用中の参考書/問題集 (継続活用を前提とすること):\n${lines.join('\n')}\n→ これらの教材は既に持っている前提で計画に組み込み、不足分のみ新規提案すること。`;
      }
    } catch (_) { /* マイ参考書取得失敗時は無視して通常生成 */ }
    const sysPrompt = '受験戦略を立てる学習プランナーです。指定の志望校に必要な科目構成を考慮し、現実的な学習計画を立てます。教師名や塾名は出さず、純粋な JSON だけ返答します。';
    // 2026-05-07 致命修正: max_tokens を 2500→4500 に増量
    // (3〜5件 × 9 field の JSON は出力 3000-4000 token 必要・2500 だと途中で切れて parse 失敗していた)
    // 同時に rationale を 40 文字以内に短縮 + color は省略可に変更してトークン節約
    const userPrompt = `志望校: ${goal}\n${material ? '優先教材: ' + material + '\n' : ''}期間: ${start} 〜 ${end} (${days}日間)\n1日確保時間: ${dailyMin} 分 (期間総計 ${totalMin} 分)${ownMaterialsSnippet}\n\n上記期間に並列で進めるべき計画を 3〜4件 提案してください。各計画は study_plans に登録される単位 (1 教材 or 1 単元 単位)。\n\n出力形式 (フェンスや前置きなし、純粋な JSON だけ・改行最小):\n[\n  {\n    "title": "タイトル(40文字以内)",\n    "subject": "次から1つ: 英語/数学/国語/現代文/古文/漢文/理科/物理/化学/生物/地学/社会/日本史/世界史/地理/倫理/政経/情報/小論文/面接対策/その他",\n    "material": "推奨教材名(40文字以内)",\n    "start_date": "${start}",\n    "end_date": "YYYY-MM-DD",\n    "target_minutes": 整数,\n    "target_pages": 整数 or null,\n    "color": "#6366f1(英)/#10b981(数)/#ec4899(国)/#f59e0b(理)/#8b5cf6(社) 該当色",\n    "rationale": "理由(40文字以内)"\n  }\n]\n注: target_minutes 合計は期間総計の 80〜100%。期間 30日以下なら 3件、それ以上 4件。短文・簡潔に。`;
    // max_tokens を 4500 に増量 (Gemini truncation 対策)
    const proposals = await _spCallAi(sysPrompt, userPrompt, 4500);
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
  // 📅 隔日学習計画: form reset 時に week_pattern も 'all' (毎日) に戻す
  _setWeekPatternUI('all');
}

// 📅 隔日学習計画 (2026-05-22 塾長指示): week_pattern UI helpers
function _setWeekPatternUI(pattern) {
  const wpInput = document.getElementById('spWeekPattern');
  if (wpInput) wpInput.value = pattern || 'all';
  // checkbox 反映
  const days = (pattern && pattern !== 'all') ? String(pattern).split(',').map(d => parseInt(d, 10)) : [1,2,3,4,5,6,7];
  document.querySelectorAll('.sp-wp-day').forEach(cb => {
    const d = parseInt(cb.dataset.day, 10);
    cb.checked = (pattern === 'all') ? false : days.includes(d);
  });
  // preset ボタンの active 状態
  document.querySelectorAll('.sp-wp-preset').forEach(btn => {
    const isActive = btn.dataset.pattern === (pattern || 'all');
    btn.style.opacity = isActive ? '1' : '0.55';
    btn.style.transform = isActive ? 'scale(1.05)' : 'scale(1)';
  });
}

function _bindWeekPatternUI() {
  document.querySelectorAll('.sp-wp-preset').forEach(btn => {
    if (btn._wpBound) return;
    btn.addEventListener('click', () => _setWeekPatternUI(btn.dataset.pattern));
    btn._wpBound = true;
  });
  document.querySelectorAll('.sp-wp-day').forEach(cb => {
    if (cb._wpBound) return;
    cb.addEventListener('change', () => {
      const checked = Array.from(document.querySelectorAll('.sp-wp-day:checked'))
        .map(c => parseInt(c.dataset.day, 10))
        .sort();
      const pattern = (checked.length === 0 || checked.length === 7) ? 'all' : checked.join(',');
      const wpInput = document.getElementById('spWeekPattern');
      if (wpInput) wpInput.value = pattern;
      // preset 同期 (custom 入力時は preset 全部非 active)
      document.querySelectorAll('.sp-wp-preset').forEach(b => {
        const isActive = b.dataset.pattern === pattern;
        b.style.opacity = isActive ? '1' : '0.55';
        b.style.transform = isActive ? 'scale(1.05)' : 'scale(1)';
      });
    });
    cb._wpBound = true;
  });
  // 初期 active 表示 (毎日 default)
  _setWeekPatternUI('all');
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

  // 📅 隔日学習計画 (2026-05-22 塾長指示): week_pattern を form から取得
  const wpInput = document.getElementById('spWeekPattern');
  const week_pattern = (wpInput && wpInput.value) || 'all';

  const body = {
    title, subject,
    material: material || undefined,
    start_date, end_date,
    target_minutes: target_minutes_raw ? parseInt(target_minutes_raw, 10) : undefined,
    target_pages: target_pages_raw ? parseInt(target_pages_raw, 10) : undefined,
    color, note: note || undefined,
    week_pattern,
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

// 📅 隔日学習計画 helper (2026-05-22 塾長指示): week_pattern → 表示文字列
function _formatWeekPattern(pattern) {
  if (!pattern || pattern === 'all') return '毎日';
  const names = {1:'月',2:'火',3:'水',4:'木',5:'金',6:'土',7:'日'};
  const days = String(pattern).split(',').map(d => parseInt(d, 10)).filter(d => d>=1 && d<=7).sort();
  if (!days.length) return '毎日';
  const key = days.join(',');
  if (key === '1,2,3,4,5') return '平日';
  if (key === '6,7') return '週末';
  if (key === '1,3,5') return '月水金';
  if (key === '2,4,6') return '火木土';
  return days.map(d => names[d]).join('');
}

// 「今日学習する日か」(week_pattern と現在の曜日を比較)
// 🛡️ 2026-05-22 fix: ブラウザ TZ ではなく JST (Asia/Tokyo) で曜日判定。
// 海外在住・端末 TZ ズレ・JST 深夜帯で「今日の学習日」誤判定を防ぐ。
// _slJstDate(0) で 'YYYY-MM-DD' (JST) を取得 → noon UTC で Date 化して getUTCDay() で曜日抽出。
// (時刻部分は 12:00 UTC 固定なので DST 等の影響を受けず安全)
function _isTodayLearningDay(pattern) {
  if (!pattern || pattern === 'all') return true;
  const jstYmd = _slJstDate(0); // 'YYYY-MM-DD' (JST)
  const d = new Date(jstYmd + 'T12:00:00Z'); // noon UTC で固定 → 曜日は JST と同一日付
  const dayNum = d.getUTCDay(); // 0=日, 1=月..6=土
  const iso = dayNum === 0 ? 7 : dayNum; // 1=月..7=日 に正規化
  const days = String(pattern).split(',').map(d => parseInt(d, 10));
  return days.includes(iso);
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
    // 📅 隔日学習計画 (2026-05-22 塾長指示)
    const wp = p.week_pattern || 'all';
    const wpLabel = _formatWeekPattern(wp);
    const isToday = p.status === 'active' && _isTodayLearningDay(wp);
    const cardBg = isToday ? 'rgba(34,197,94,0.08)' : 'rgba(255,255,255,0.04)';
    const cardBorder = isToday ? '4px solid #22c55e' : `4px solid ${escapeHtml(p.color)}`;
    return `
      <div style="background:${cardBg}; border-left:${cardBorder}; border-radius:8px; padding:0.85rem; margin-bottom:0.6rem;">
        <div style="display:flex; justify-content:space-between; align-items:start; margin-bottom:0.4rem;">
          <div style="flex:1;">
            <div style="font-weight:700; color:#e4e4e7; font-size:0.95rem;">${isToday ? '<span style="color:#86efac;margin-right:0.3rem;">🟢</span>' : ''}${escapeHtml(p.title)}</div>
            <div style="font-size:0.78rem; color:#a1a1aa; margin-top:0.2rem;">
              <span style="background:rgba(99,102,241,0.2); color:#c7d2fe; padding:0.1rem 0.4rem; border-radius:4px; font-size:0.72rem;">${escapeHtml(p.subject)}</span>
              <span style="background:${wp==='all'?'rgba(148,163,184,0.2)':'rgba(167,139,250,0.22)'}; color:${wp==='all'?'#cbd5e1':'#c4b5fd'}; padding:0.1rem 0.4rem; border-radius:4px; font-size:0.72rem; margin-left:0.3rem;">📅 ${escapeHtml(wpLabel)}</span>
              ${p.material ? `<span style="margin-left:0.3rem;">${escapeHtml(p.material)}</span>` : ''}
            </div>
            <div style="font-size:0.75rem; color:#71717a; margin-top:0.2rem;">
              ${escapeHtml(p.start_date)} 〜 ${escapeHtml(p.end_date)}
              ${p.status === 'active' ? `<span style="color:${remainDays <= 7 ? '#fca5a5' : '#a1a1aa'}; margin-left:0.5rem;">残り ${remainDays} 日</span>` : ''}
              ${isToday ? '<span style="color:#86efac;margin-left:0.5rem;font-weight:700;">📌 今日の学習日</span>' : ''}
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
    // 📅 隔日学習計画: week_pattern を form に反映
    _setWeekPatternUI(plan.week_pattern || 'all');
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
  _initComposeUI();
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

// ✏️ 送信フォーム初期化 (kokuritsu_nankan 受講生向け)
function _initComposeUI() {
  const composeBtn = document.getElementById('msgComposeBtn');
  const composeHint = document.getElementById('msgComposeHint');
  const composeForm = document.getElementById('msgComposeForm');
  const cancelBtn = document.getElementById('msgComposeCancel');
  const submitBtn = document.getElementById('msgComposeSubmit');
  const fileInput = document.getElementById('msgComposeFile');
  const fileNameLabel = document.getElementById('msgComposeFileName');
  if (!composeBtn || !composeForm) return;
  // 塾長との双方向メッセージは本クラス所属生徒のみ表示 (premium 等の有料プランでは非表示)
  const tryShow = (retries) => {
    const student = (window.AuthGuard && window.AuthGuard.getStudent && window.AuthGuard.getStudent()) || null;
    if (!student && retries > 0) { setTimeout(() => tryShow(retries - 1), 200); return; }
    if (_canUseTeacherMessaging(student)) {
      composeBtn.style.display = '';
      if (composeHint) composeHint.style.display = '';
    }
  };
  tryShow(10);
  if (!composeBtn._bound) {
    composeBtn._bound = true;
    composeBtn.addEventListener('click', () => {
      composeForm.style.display = '';
      composeBtn.style.display = 'none';
    });
  }
  if (cancelBtn && !cancelBtn._bound) {
    cancelBtn._bound = true;
    cancelBtn.addEventListener('click', () => {
      composeForm.style.display = 'none';
      composeBtn.style.display = '';
      _resetComposeForm();
    });
  }
  if (fileInput && !fileInput._bound) {
    fileInput._bound = true;
    fileInput.addEventListener('change', (e) => {
      const f = e.target.files && e.target.files[0];
      if (!f) { fileNameLabel.textContent = ''; return; }
      if (f.size > 10 * 1024 * 1024) {
        fileNameLabel.textContent = `❌ ファイルが大きすぎます (${(f.size/1024/1024).toFixed(1)} MB / 上限 10 MB)`;
        fileNameLabel.style.color = '#fca5a5';
        fileInput.value = '';
        return;
      }
      fileNameLabel.textContent = `📎 ${f.name} (${(f.size/1024).toFixed(1)} KB)`;
      fileNameLabel.style.color = '#86efac';
    });
  }
  if (submitBtn && !submitBtn._bound) {
    submitBtn._bound = true;
    submitBtn.addEventListener('click', _submitComposeMessage);
  }
}

function _resetComposeForm() {
  ['msgComposeSubject', 'msgComposeBody'].forEach(id => { const el = document.getElementById(id); if (el) el.value = ''; });
  const fileInput = document.getElementById('msgComposeFile');
  if (fileInput) fileInput.value = '';
  const fileLabel = document.getElementById('msgComposeFileName');
  if (fileLabel) { fileLabel.textContent = ''; }
  const status = document.getElementById('msgComposeStatus');
  if (status) status.textContent = '';
}

async function _submitComposeMessage() {
  const subject = (document.getElementById('msgComposeSubject').value || '').trim();
  const body = (document.getElementById('msgComposeBody').value || '').trim();
  const fileInput = document.getElementById('msgComposeFile');
  const file = fileInput && fileInput.files && fileInput.files[0];
  const submitBtn = document.getElementById('msgComposeSubmit');
  const status = document.getElementById('msgComposeStatus');
  if (!body) {
    status.innerHTML = '<span style="color:#fca5a5;">本文を入力してください</span>';
    return;
  }
  if (file && file.size > 10 * 1024 * 1024) {
    status.innerHTML = '<span style="color:#fca5a5;">添付ファイルは 10 MB まで</span>';
    return;
  }
  submitBtn.disabled = true;
  const orig = submitBtn.textContent;
  submitBtn.textContent = '⏳ 送信中...';
  status.innerHTML = '<span style="color:#a1a1aa;">送信中...</span>';
  const payload = { subject: subject || undefined, body };
  if (file) {
    try {
      const dataUrl = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = () => reject(new Error('ファイル読込失敗'));
        reader.readAsDataURL(file);
      });
      const b64 = String(dataUrl).split(',')[1] || '';
      payload.attachment_filename = file.name;
      payload.attachment_mime = file.type || 'application/octet-stream';
      payload.attachment_data_b64 = b64;
    } catch (e) {
      status.innerHTML = `<span style="color:#fca5a5;">ファイル読込失敗: ${escapeHtml(e.message || '')}</span>`;
      submitBtn.disabled = false; submitBtn.textContent = orig; return;
    }
  }
  try {
    const r = await slApiFetch('/api/student/messages/send', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    status.innerHTML = `<span style="color:#86efac;">✅ ${escapeHtml(r.info || '送信完了')}</span>`;
    _resetComposeForm();
    // フォームを閉じて受信箱を再読込
    setTimeout(() => {
      document.getElementById('msgComposeForm').style.display = 'none';
      const cb = document.getElementById('msgComposeBtn');
      if (cb) cb.style.display = '';
      loadMyMessages();
    }, 1200);
  } catch (e) {
    status.innerHTML = `<span style="color:#fca5a5;">❌ 送信失敗: ${escapeHtml(e.message || '')}</span>`;
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = orig;
  }
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
      const isOut = m.direction === 'out';
      const unreadBorder = m.is_unread ? 'border-left:4px solid #ec4899;'
        : (isOut ? 'border-left:4px solid rgba(167,139,250,0.5);' : 'border-left:4px solid rgba(255,255,255,0.05);');
      const dotBadge = m.is_unread ? '<span class="msg-unread-dot" style="display:inline-block; width:8px; height:8px; background:#ec4899; border-radius:50%; margin-right:0.4rem; vertical-align:middle;"></span>' : '';
      const dirBadge = isOut
        ? '<span style="background:rgba(167,139,250,0.2); color:#c4b5fd; padding:0.1rem 0.5rem; border-radius:4px; font-size:0.7em; margin-right:0.4rem; vertical-align:middle;">📤 送信済</span>'
        : '';
      const att = m.attachment;
      const attBlock = att
        ? `<div class="msg-attachment" style="margin-top:0.5rem; padding:0.5rem 0.7rem; background:rgba(0,0,0,0.3); border-radius:6px; display:flex; justify-content:space-between; align-items:center; gap:0.5rem;">
            <span style="font-size:0.8rem; color:#cbd5e1;">📎 ${escapeHtml(att.filename)} <span style="color:#71717a; font-size:0.85em;">(${Math.round((att.size||0)/1024)} KB)</span></span>
            <button type="button" data-msg-id="${m.id}" class="msg-att-dl" style="background:rgba(99,102,241,0.25); color:#c7d2fe; border:0; padding:0.3rem 0.7rem; border-radius:6px; cursor:pointer; font-size:0.78rem; font-weight:700;">⬇️ ダウンロード</button>
          </div>`
        : '';
      return `
        <div data-msg-id="${m.id}" data-unread="${m.is_unread ? '1' : '0'}" class="msg-item" style="background:rgba(255,255,255,0.04); ${unreadBorder} border-radius:8px; padding:0.85rem; margin-bottom:0.6rem; cursor:pointer;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.3rem;">
            <div style="font-weight:700; color:#c7d2fe; font-size:0.9rem;">${dotBadge}${dirBadge}${escapeHtml(m.subject || 'お知らせ')}</div>
            <div style="font-size:0.72rem; color:#71717a;">${escapeHtml(_fmtJstYMDHM(m.created_at))}</div>
          </div>
          <div class="msg-body" style="font-size:0.85rem; color:#d4d4d8; white-space:pre-wrap; max-height:3em; overflow:hidden; text-overflow:ellipsis; transition:max-height 0.3s;">${escapeHtml(m.body)}</div>
          ${attBlock}
        </div>`;
    }).join('');
    // 添付 DL ボタン bind (クリックの bubble を止めて行展開と分離)
    list.querySelectorAll('.msg-att-dl').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.stopPropagation();
        const id = btn.getAttribute('data-msg-id');
        const orig = btn.textContent;
        btn.disabled = true;
        btn.textContent = '⏳ 取得中...';
        try {
          const apiBase = (window.location.origin.includes(':8090') || window.location.origin.includes('localhost:8090'))
            ? 'http://localhost:8000' : window.location.origin;
          const token = (window.AuthGuard && window.AuthGuard.getToken && window.AuthGuard.getToken()) || localStorage.getItem('ai_juku_session_token');
          const r = await fetch(apiBase + `/api/messages/me/${encodeURIComponent(id)}/attachment`, {
            headers: { 'Authorization': 'Bearer ' + token },
          });
          if (!r.ok) throw new Error('HTTP ' + r.status);
          const blob = await r.blob();
          // Content-Disposition から filename を抽出
          const cd = r.headers.get('content-disposition') || '';
          let fn = 'attachment';
          const m1 = cd.match(/filename\*=UTF-8''([^;]+)/i);
          if (m1) { try { fn = decodeURIComponent(m1[1]); } catch {} }
          else { const m2 = cd.match(/filename="?([^";]+)/i); if (m2) fn = m2[1]; }
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url; a.download = fn; document.body.appendChild(a); a.click(); a.remove();
          setTimeout(() => URL.revokeObjectURL(url), 1500);
        } catch (e) {
          alert('ダウンロード失敗: ' + (e.message || e));
        } finally {
          btn.disabled = false;
          btn.textContent = orig;
        }
      });
    });
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


// ==========================================================================
// 🎓 合格カリキュラム (Phase 4 - 国公立難関大学コース限定 / 難関私立も対象)
// ==========================================================================
function initCurriculum() {
  // 🚨 2026-05-13 塾長指示「絶対に消えない」: section の display は **絶対に none にしない**。
  const section = document.querySelector('.curriculum-section');
  if (section) section.style.display = '';  // 初期から表示
  const tryInit = (retries) => {
    const student = (window.AuthGuard && window.AuthGuard.getStudent && window.AuthGuard.getStudent()) || null;
    if (!student) {
      // ⚠️ auth pending: hide しない (元 HTML のまま polling 継続)
      if (retries > 0) setTimeout(() => tryInit(retries - 1), 200);
      return;
    }
    if (typeof student.course === 'undefined' && retries > 0) {
      setTimeout(() => tryInit(retries - 1), 200);
      return;
    }
    if (!_canUseStudyMgmt(student)) {
      if (section) {
        section.style.display = '';
        section.innerHTML = `
          <div class="section-title"><h2>🎓 合格カリキュラム <span style="font-size:0.65em;background:linear-gradient(135deg,#fbbf24,#ec4899);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-weight:800;">プレミアム限定</span></h2></div>
          <div style="padding:1.2rem; background:rgba(251,191,36,0.06); border:1px dashed rgba(251,191,36,0.35); border-radius:12px; text-align:center;">
            <div style="font-size:2.5rem; margin-bottom:0.5rem;">🎓</div>
            <div style="color:#fbbf24; font-weight:700; font-size:1.05rem; margin-bottom:0.5rem;">入試日から逆算した合格までの全体ロードマップ</div>
            <p style="color:#a1a1aa; font-size:0.88rem; margin:0.5rem 0 1rem 0;">AI が入試日から逆算して 4-6 フェーズに分割し、教材・期間・マイルストーンを自動提案。プレミアムプラン以上で利用可能です。</p>
            <button type="button" class="course-inquiry-btn" data-course="kokuritsu_nankan" data-source="curriculum" style="display:inline-block; padding:0.85rem 1.5rem; background:linear-gradient(135deg,#fbbf24,#ec4899); color:#fff; border:0; border-radius:10px; font-weight:700; font-size:0.95rem; cursor:pointer; box-shadow:0 4px 12px rgba(236,72,153,0.3);">⭐ プレミアムにアップグレード</button>
            <div class="course-inquiry-msg" style="margin-top:0.7rem; font-size:0.82rem;"></div>
          </div>`;
        bindCourseInquiryButtons(section);
      }
      return;
    }
    if (section) section.style.display = '';
    bindCurriculumButtons();
    loadMyCurricula();
  };
  tryInit(10);
}

let _cuLastList = [];
let _cuLastPreview = null;

function bindCurriculumButtons() {
  // 📚 マイ参考書 UI (カリキュラム生成フォーム内・塾長指示 2026-05-14)
  // 学習計画タブを開いてない生徒でも、カリキュラム生成画面から直接登録できるよう init
  initMyMaterials('cum');
  loadMyMaterials();
  const toggleBtn = document.getElementById('cuToggleAiBtn');
  const cancelBtn = document.getElementById('cuAiCancelBtn');
  const submitBtn = document.getElementById('cuAiGenSubmit');
  if (toggleBtn && !toggleBtn._cuBound) {
    toggleBtn.addEventListener('click', () => {
      const w = document.getElementById('cuAiWrap');
      const isOpen = w.style.display !== 'none';
      w.style.display = isOpen ? 'none' : '';
      if (!isOpen) {
        // default values
        const today = _slJstDate(0);
        if (!document.getElementById('cuAiStart').value) document.getElementById('cuAiStart').value = today;
        if (!document.getElementById('cuAiDailyMin').value) document.getElementById('cuAiDailyMin').value = '60';
      }
    });
    toggleBtn._cuBound = true;
  }
  if (cancelBtn && !cancelBtn._cuBound) {
    cancelBtn.addEventListener('click', () => { document.getElementById('cuAiWrap').style.display = 'none'; });
    cancelBtn._cuBound = true;
  }
  if (submitBtn && !submitBtn._cuBound) {
    submitBtn.addEventListener('click', generateCurriculumWithAi);
    submitBtn._cuBound = true;
  }

  // 🗓 2026-05-30: 曜日別カスタマイズ toggle + 自動計算
  const dowToggle = document.getElementById('cuToggleByDowBtn');
  if (dowToggle && !dowToggle._cuBound) {
    dowToggle.addEventListener('click', () => {
      const wrap = document.getElementById('cuByDowWrap');
      const arrow = document.getElementById('cuToggleByDowArrow');
      const isOpen = wrap.style.display !== 'none';
      wrap.style.display = isOpen ? 'none' : 'block';
      if (arrow) arrow.textContent = isOpen ? '▼' : '▲';
      if (!isOpen) {
        // 開いた時に既存の daily_minutes でプリフィル (空欄のみ)
        const daily = parseInt(document.getElementById('cuAiDailyMin').value, 10) || 60;
        for (let i = 1; i <= 7; i++) {
          const el = document.getElementById('cuDow' + i);
          if (el && !el.value) el.value = (i >= 6 ? Math.min(daily * 2, 720) : daily); // 土日は 2 倍を提案
        }
        _cuRecalcDowTotal();
      }
    });
    dowToggle._cuBound = true;
  }
  // 各 input 変更で自動計算
  for (let i = 1; i <= 7; i++) {
    const el = document.getElementById('cuDow' + i);
    if (el && !el._cuBound) {
      el.addEventListener('input', _cuRecalcDowTotal);
      el._cuBound = true;
    }
  }
  // リセット (均等に戻す) ボタン
  const clearBtn = document.getElementById('cuDowClearBtn');
  if (clearBtn && !clearBtn._cuBound) {
    clearBtn.addEventListener('click', () => {
      for (let i = 1; i <= 7; i++) {
        const el = document.getElementById('cuDow' + i);
        if (el) el.value = '';
      }
      document.getElementById('cuByDowWrap').style.display = 'none';
      const arrow = document.getElementById('cuToggleByDowArrow');
      if (arrow) arrow.textContent = '▼';
    });
    clearBtn._cuBound = true;
  }
}

function _cuRecalcDowTotal() {
  let total = 0;
  let filled = 0;
  for (let i = 1; i <= 7; i++) {
    const el = document.getElementById('cuDow' + i);
    const n = el ? parseInt(el.value, 10) : NaN;
    if (!isNaN(n) && n >= 0) { total += Math.min(n, 720); filled++; }
  }
  const totalEl = document.getElementById('cuDowWeekTotal');
  const avgEl = document.getElementById('cuDowDailyAvg');
  if (totalEl) totalEl.textContent = String(total);
  if (avgEl) avgEl.textContent = String(filled > 0 ? Math.round(total / 7) : 0);
}

async function generateCurriculumWithAi() {
  const btn = document.getElementById('cuAiGenSubmit');
  const msg = document.getElementById('cuAiMsg');
  const previewEl = document.getElementById('cuAiPreview');
  if (!btn || btn.disabled) return;
  const univ = document.getElementById('cuAiUniv').value.trim();
  const faculty = document.getElementById('cuAiFaculty').value.trim();
  const start = document.getElementById('cuAiStart').value;
  const exam = document.getElementById('cuAiExam').value;
  const dailyMin = parseInt(document.getElementById('cuAiDailyMin').value, 10) || 60;
  const baseline = document.getElementById('cuAiBaseline').value.trim();

  if (!univ) { msg.style.color = '#fca5a5'; msg.textContent = '志望校は必須です'; return; }
  if (!exam) { msg.style.color = '#fca5a5'; msg.textContent = '入試日は必須です'; return; }
  if (start && exam <= start) { msg.style.color = '#fca5a5'; msg.textContent = '入試日は開始日より後である必要があります'; return; }

  // 🗓 2026-05-30: 曜日別カスタマイズが有効なら weekly_minutes 配列を送信
  let weeklyMinutes = null;
  const byDowWrap = document.getElementById('cuByDowWrap');
  if (byDowWrap && byDowWrap.style.display !== 'none') {
    const _wm = [];
    let _hasAny = false;
    for (let i = 1; i <= 7; i++) {
      const _v = document.getElementById('cuDow' + i);
      const _n = _v ? parseInt(_v.value, 10) : NaN;
      if (!isNaN(_n) && _n >= 0) { _wm.push(Math.min(_n, 720)); _hasAny = true; }
      else _wm.push(dailyMin);  // 空欄は daily_minutes で補完
    }
    if (_hasAny) weeklyMinutes = _wm;
  }

  btn.disabled = true; btn.textContent = '🤖 AI 生成中... (15-40秒)';
  msg.style.color = '#c4b5fd'; msg.textContent = '🤖 入試日から逆算してフェーズ分割しています...';
  previewEl.innerHTML = '';
  try {
    const data = await slApiFetch('/api/curricula/ai-generate', {
      method: 'POST',
      body: JSON.stringify({
        target_university: univ,
        target_faculty: faculty || undefined,
        exam_date: exam,
        start_date: start || undefined,
        daily_minutes: dailyMin,
        weekly_minutes: weeklyMinutes || undefined,
        baseline_note: baseline || undefined,
      }),
    });
    const preview = data.preview;
    _cuLastPreview = preview;
    if (!preview || !preview.phases || !preview.phases.length) throw new Error('AI が phases を返しませんでした');
    msg.style.color = '#86efac'; msg.textContent = `✅ ${preview.phases.length} フェーズの合格カリキュラムを生成しました (プレビュー → 保存ボタンで確定)`;
    previewEl.innerHTML = renderCurriculumPreview(preview);
    document.getElementById('cuPreviewSaveBtn').addEventListener('click', saveCurriculumFromPreview);
  } catch (e) {
    msg.style.color = '#fca5a5';
    msg.textContent = '❌ ' + (e.message || '生成失敗');
    // 🔧 2026-05-14 塾長指示: 503 (AI 生成失敗) 時に「もう一度試す」ボタンを即提示
    // 単発失敗は AI 一時的不調が主因 → リトライで多くは解消
    const isRetryable = e && e.status === 503;
    if (isRetryable && previewEl) {
      previewEl.innerHTML = `
        <div style="margin-top:0.6rem; padding:0.8rem; background:rgba(251,113,133,0.08); border:1px solid rgba(251,113,133,0.3); border-radius:8px; text-align:center;">
          <p style="margin:0 0 0.5rem 0; font-size:0.85rem; color:#fda4af;">AI が一時的に応答できませんでした。再試行で多くは解消されます。</p>
          <button id="cuRetryBtn" type="button" style="padding:0.55rem 1.2rem; background:linear-gradient(135deg,#a78bfa,#ec4899); border:0; border-radius:8px; color:#fff; font-weight:700; font-size:0.85rem; cursor:pointer;">↻ もう一度試す</button>
        </div>`;
      const retryBtn = document.getElementById('cuRetryBtn');
      if (retryBtn) retryBtn.addEventListener('click', () => { previewEl.innerHTML = ''; generateCurriculumWithAi(); });
    }
  } finally {
    btn.disabled = false; btn.textContent = '✨ カリキュラムを生成する';
  }
}

function renderCurriculumPreview(c) {
  const examDate = c.exam_date;
  const startDate = c.start_date;
  const today = _slJstDate(0);
  const remainDays = Math.max(0, Math.ceil((new Date(examDate) - new Date(today)) / 86400000));
  return `
    <div style="background:rgba(0,0,0,0.3); border-radius:10px; padding:1rem; margin-top:0.5rem;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.6rem;">
        <div style="font-weight:800; color:#fbbf24; font-size:1.05rem;">🎓 ${escapeHtml(c.target_university)}${c.target_faculty ? ` <span style="color:#a1a1aa; font-size:0.85rem;">${escapeHtml(c.target_faculty)}</span>` : ''}</div>
        <div style="font-size:0.75rem; color:#a1a1aa;">入試まで <strong style="color:#ec4899;">${remainDays}日</strong></div>
      </div>
      <div style="font-size:0.78rem; color:#a1a1aa; margin-bottom:0.7rem;">${escapeHtml(startDate)} 〜 ${escapeHtml(examDate)} ・ 1日 ${c.daily_minutes}分</div>
      ${c.phases.map((p, i) => `
        <div style="background:rgba(255,255,255,0.04); border-left:4px solid #a78bfa; border-radius:8px; padding:0.7rem; margin-bottom:0.5rem;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.3rem;">
            <div style="font-weight:700; color:#c4b5fd;">${i + 1}. ${escapeHtml(p.name)}</div>
            <div style="font-size:0.72rem; color:#71717a;">${escapeHtml(p.start_date)} 〜 ${escapeHtml(p.end_date)}</div>
          </div>
          <div style="font-size:0.85rem; color:#e4e4e7; margin-bottom:0.4rem;">🎯 ${escapeHtml(p.focus)}</div>
          ${p.materials && p.materials.length ? `<div style="font-size:0.78rem; color:#a1a1aa; margin-bottom:0.3rem;">📚 市販教材: ${p.materials.map(m => `<span style="background:rgba(99,102,241,0.15); color:#c7d2fe; padding:0.1rem 0.4rem; border-radius:4px; margin-right:0.2rem; display:inline-block; margin-bottom:0.2rem;">${escapeHtml(m)}</span>`).join('')}</div>` : ''}
          ${p.sapuri_lectures && p.sapuri_lectures.length ? `<div style="font-size:0.78rem; color:#a1a1aa; margin-bottom:0.3rem;">📺 スタサプ講義: ${p.sapuri_lectures.map(m => `<span style="background:rgba(251,113,133,0.15); color:#fda4af; padding:0.1rem 0.4rem; border-radius:4px; margin-right:0.2rem; display:inline-block; margin-bottom:0.2rem;">${escapeHtml(m)}</span>`).join('')}</div>` : ''}
          ${p.milestones && p.milestones.length ? `<div style="font-size:0.78rem; color:#a1a1aa;">📌 マイルストーン: <ul style="margin:0.2rem 0 0 1rem; padding:0;">${p.milestones.map(m => `<li>${escapeHtml(m)}</li>`).join('')}</ul></div>` : ''}
        </div>
      `).join('')}
      <button id="cuPreviewSaveBtn" type="button" style="width:100%; margin-top:0.5rem; padding:0.75rem; background:linear-gradient(135deg,#10b981,#34d399); border:0; border-radius:8px; color:#fff; font-weight:800; cursor:pointer;">✅ このカリキュラムで保存する</button>
      <div id="cuPreviewSaveMsg" style="margin-top:0.4rem; font-size:0.78rem; min-height:1em;"></div>
    </div>`;
}

async function saveCurriculumFromPreview() {
  if (!_cuLastPreview) return;
  const btn = document.getElementById('cuPreviewSaveBtn');
  const msg = document.getElementById('cuPreviewSaveMsg');
  btn.disabled = true; btn.textContent = '保存中...';
  try {
    await slApiFetch('/api/curricula', {
      method: 'POST',
      body: JSON.stringify({
        target_university: _cuLastPreview.target_university,
        target_faculty: _cuLastPreview.target_faculty,
        exam_date: _cuLastPreview.exam_date,
        start_date: _cuLastPreview.start_date,
        daily_minutes: _cuLastPreview.daily_minutes,
        weekly_minutes: _cuLastPreview.weekly_minutes || undefined,  // 🗓 2026-05-30
        baseline_note: _cuLastPreview.baseline_note,
        phases: _cuLastPreview.phases,
        ai_model: _cuLastPreview.ai_model,
      }),
    });
    if (msg) { msg.style.color = '#86efac'; msg.textContent = '✅ カリキュラムを保存しました'; }
    document.getElementById('cuAiWrap').style.display = 'none';
    _cuLastPreview = null;
    await loadMyCurricula();
  } catch (e) {
    if (msg) { msg.style.color = '#fca5a5'; msg.textContent = '❌ 保存失敗: ' + (e.message || ''); }
    btn.disabled = false; btn.textContent = '✅ このカリキュラムで保存する';
  }
}

async function loadMyCurricula() {
  const list = document.getElementById('cuList');
  if (!list) return;
  try {
    const data = await slApiFetch('/api/curricula/me');
    const items = data.curricula || [];
    _cuLastList = items;
    if (!items.length) {
      list.innerHTML = '<div style="text-align:center; color:#71717a; padding:1.5rem; background:rgba(0,0,0,0.2); border-radius:10px;">🎓 カリキュラムがまだありません。「🤖 AI に作ってもらう」から生成してみよう！</div>';
      return;
    }
    const today = _slJstDate(0);
    list.innerHTML = items.map(c => {
      const remainDays = Math.max(0, Math.ceil((new Date(c.exam_date) - new Date(today)) / 86400000));
      const totalDays = Math.max(1, Math.ceil((new Date(c.exam_date) - new Date(c.start_date)) / 86400000));
      const elapsedDays = Math.max(0, Math.min(totalDays, Math.ceil((new Date(today) - new Date(c.start_date)) / 86400000)));
      const dayPct = Math.round(elapsedDays / totalDays * 100);
      const statusBadge = c.status === 'active' ? '<span style="background:rgba(134,239,172,0.18); color:#86efac; padding:0.15rem 0.5rem; border-radius:999px; font-size:0.7rem; font-weight:700;">進行中</span>'
        : c.status === 'completed' ? '<span style="background:rgba(56,189,248,0.18); color:#7dd3fc; padding:0.15rem 0.5rem; border-radius:999px; font-size:0.7rem; font-weight:700;">完了</span>'
        : '<span style="background:rgba(113,113,122,0.18); color:#a1a1aa; padding:0.15rem 0.5rem; border-radius:999px; font-size:0.7rem; font-weight:700;">アーカイブ</span>';
      // 現在のフェーズ判定
      const currentPhase = (c.phases || []).find(p => p.start_date <= today && today <= p.end_date) || (c.phases || []).find(p => today < p.start_date);
      return `
        <div style="background:rgba(255,255,255,0.04); border:1px solid rgba(167,139,250,0.3); border-left:4px solid #a78bfa; border-radius:10px; padding:1rem; margin-bottom:0.7rem;">
          <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:0.5rem; flex-wrap:wrap; gap:0.4rem;">
            <div style="flex:1;">
              <div style="font-weight:800; color:#fbbf24; font-size:1.05rem;">🎓 ${escapeHtml(c.target_university)}${c.target_faculty ? ` <span style="color:#a1a1aa; font-size:0.85rem;">${escapeHtml(c.target_faculty)}</span>` : ''} ${statusBadge}</div>
              <div style="font-size:0.75rem; color:#a1a1aa; margin-top:0.2rem;">${escapeHtml(c.start_date)} 〜 ${escapeHtml(c.exam_date)} ・ 1日 ${c.daily_minutes || 60}分</div>
              ${currentPhase ? `<div style="font-size:0.85rem; color:#c4b5fd; margin-top:0.3rem;">📍 現在: <strong>${escapeHtml(currentPhase.name)}</strong> ${currentPhase.start_date <= today ? '(進行中)' : '(まだ先)'}</div>` : ''}
            </div>
            <div style="text-align:right;">
              <div style="font-size:1.4rem; font-weight:800; color:#ec4899;">${remainDays}日</div>
              <div style="font-size:0.7rem; color:#71717a;">入試まで</div>
            </div>
          </div>
          <div style="background:rgba(0,0,0,0.3); border-radius:6px; height:8px; overflow:hidden; margin-bottom:0.5rem;">
            <div style="background:linear-gradient(90deg,#a78bfa,#ec4899); height:100%; width:${dayPct}%;"></div>
          </div>
          <div style="display:flex; gap:0.4rem; flex-wrap:wrap; margin-bottom:0.5rem;">
            <button data-id="${c.id}" class="cu-detail-btn" style="background:rgba(99,102,241,0.2); color:#c7d2fe; border:0; padding:0.4rem 0.8rem; border-radius:6px; cursor:pointer; font-size:0.78rem;">📖 詳細を見る</button>
            <button data-id="${c.id}" class="cu-gap-btn" style="background:linear-gradient(135deg,#a78bfa,#ec4899); color:#fff; border:0; padding:0.4rem 0.8rem; border-radius:6px; cursor:pointer; font-size:0.78rem; font-weight:700;">🤖 AI ギャップ分析</button>
            <button data-id="${c.id}" class="cu-expand-btn" style="background:linear-gradient(135deg,#10b981,#34d399); color:#fff; border:0; padding:0.4rem 0.8rem; border-radius:6px; cursor:pointer; font-size:0.78rem; font-weight:700;">📅 学習計画に展開</button>
            <button data-id="${c.id}" class="cu-delete-btn" style="background:rgba(239,68,68,0.15); color:#fca5a5; border:0; padding:0.4rem 0.8rem; border-radius:6px; cursor:pointer; font-size:0.78rem;">🗑 削除</button>
          </div>
          <div id="cuDetail-${c.id}" style="display:none; margin-top:0.6rem;">
            ${(c.phases || []).map((p, i) => `
              <div style="background:rgba(0,0,0,0.25); border-left:3px solid ${p.start_date <= today && today <= p.end_date ? '#fbbf24' : 'rgba(255,255,255,0.1)'}; border-radius:6px; padding:0.6rem; margin-bottom:0.4rem;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                  <div style="font-weight:700; color:#e4e4e7; font-size:0.88rem;">${i + 1}. ${escapeHtml(p.name)}</div>
                  <div style="font-size:0.7rem; color:#71717a;">${escapeHtml(p.start_date)}〜${escapeHtml(p.end_date)}</div>
                </div>
                <div style="font-size:0.78rem; color:#d4d4d8; margin-top:0.3rem;">🎯 ${escapeHtml(p.focus)}</div>
                ${p.materials && p.materials.length ? `<div style="font-size:0.75rem; color:#a1a1aa; margin-top:0.3rem;">📚 ${p.materials.map(m => escapeHtml(m)).join(' / ')}</div>` : ''}
                ${p.sapuri_lectures && p.sapuri_lectures.length ? `<div style="font-size:0.75rem; color:#fda4af; margin-top:0.3rem;">📺 スタサプ: ${p.sapuri_lectures.map(m => escapeHtml(m)).join(' / ')}</div>` : ''}
                ${p.milestones && p.milestones.length ? `<div style="font-size:0.75rem; color:#a1a1aa; margin-top:0.3rem;">📌 ${p.milestones.map(m => '・' + escapeHtml(m)).join(' ')}</div>` : ''}
              </div>
            `).join('')}
          </div>
        </div>`;
    }).join('');
    list.querySelectorAll('.cu-detail-btn').forEach(b => b.addEventListener('click', () => {
      const id = b.getAttribute('data-id');
      const d = document.getElementById('cuDetail-' + id);
      if (d) d.style.display = d.style.display === 'none' ? '' : 'none';
    }));
    list.querySelectorAll('.cu-expand-btn').forEach(b => b.addEventListener('click', () => expandCurriculumToPlans(b.getAttribute('data-id'))));
    list.querySelectorAll('.cu-gap-btn').forEach(b => b.addEventListener('click', () => {
      const id = b.getAttribute('data-id');
      const curr = (_cuLastList || []).find(c => String(c.id) === String(id));
      if (!curr) return;
      (async () => {
        try {
          showGapAnalysisModal('loading', { curriculum: curr });
          const data = await slApiFetch(`/api/curricula/${encodeURIComponent(id)}/gap-analyze`, { method: 'POST' });
          showGapAnalysisModal('result', { curriculum: curr, ...data });
        } catch (e) {
          showGapAnalysisModal('error', { curriculum: curr, error: e.message });
        }
      })();
    }));
    list.querySelectorAll('.cu-delete-btn').forEach(b => b.addEventListener('click', () => deleteCurriculum(b.getAttribute('data-id'))));
  } catch (e) {
    console.error('loadMyCurricula failed:', e);
    list.innerHTML = `<div style="text-align:center; color:#fca5a5; padding:1rem;">⚠️ カリキュラム読み込み失敗 (${escapeHtml(e.message || '')})</div>`;
  }
}

async function expandCurriculumToPlans(curriculumId) {
  if (!confirm('このカリキュラムの全フェーズの教材を「学習計画」に一括展開しますか?\n（既存の同名計画はスキップされます）')) return;
  try {
    const data = await slApiFetch(`/api/curricula/${encodeURIComponent(curriculumId)}/expand-to-plans`, { method: 'POST' });
    alert(`✅ ${data.added} 件の学習計画を追加しました${data.skipped ? ` (重複でスキップ ${data.skipped} 件)` : ''}`);
    await loadMyStudyPlans();
  } catch (e) {
    alert('展開失敗: ' + (e.message || ''));
  }
}

async function deleteCurriculum(curriculumId) {
  if (!confirm('このカリキュラムを削除しますか?\n（学習計画には影響しません）')) return;
  try {
    await slApiFetch(`/api/curricula/${encodeURIComponent(curriculumId)}`, { method: 'DELETE' });
    await loadMyCurricula();
  } catch (e) {
    alert('削除失敗: ' + (e.message || ''));
  }
}


// ==========================================================================
// 📊 模試結果 (Phase 4.5 - 国公立難関大学コース限定)
// ==========================================================================
let _exTrendChart = null;

function initExamResults() {
  // 🚨 2026-05-13 塾長指示「絶対に消えない」: section の display は **絶対に none にしない**。
  const section = document.querySelector('.exam-section');
  if (section) section.style.display = '';  // 初期から表示
  const tryInit = (retries) => {
    const student = (window.AuthGuard && window.AuthGuard.getStudent && window.AuthGuard.getStudent()) || null;
    if (!student) {
      // ⚠️ auth pending: hide しない (元 HTML のまま polling 継続)
      if (retries > 0) setTimeout(() => tryInit(retries - 1), 200);
      return;
    }
    if (typeof student.course === 'undefined' && retries > 0) {
      setTimeout(() => tryInit(retries - 1), 200);
      return;
    }
    if (!_canUseStudyMgmt(student)) {
      if (section) {
        section.style.display = '';
        section.innerHTML = `
          <div class="section-title"><h2>📊 模試分析 & AI弱点プリント <span style="font-size:0.65em;background:linear-gradient(135deg,#fbbf24,#ec4899);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-weight:800;">プレミアム限定</span></h2></div>
          <div style="padding:1.2rem; background:rgba(251,191,36,0.06); border:1px dashed rgba(251,191,36,0.35); border-radius:12px; text-align:center;">
            <div style="font-size:2.5rem; margin-bottom:0.5rem;">📊</div>
            <div style="color:#fbbf24; font-weight:700; font-size:1.05rem; margin-bottom:0.5rem;">模試結果から AI が弱点を自動分析</div>
            <p style="color:#a1a1aa; font-size:0.88rem; margin:0.5rem 0 1rem 0;">河合・駿台等の模試を登録 → AI が偏差値ギャップを分析し、弱点プリントを自動生成。プレミアムプラン以上で利用可能です。</p>
            <button type="button" class="course-inquiry-btn" data-course="kokuritsu_nankan" data-source="exam-analysis" style="display:inline-block; padding:0.85rem 1.5rem; background:linear-gradient(135deg,#fbbf24,#ec4899); color:#fff; border:0; border-radius:10px; font-weight:700; font-size:0.95rem; cursor:pointer; box-shadow:0 4px 12px rgba(236,72,153,0.3);">⭐ プレミアムにアップグレード</button>
            <div class="course-inquiry-msg" style="margin-top:0.7rem; font-size:0.82rem;"></div>
          </div>`;
        bindCourseInquiryButtons(section);
      }
      return;
    }
    if (section) section.style.display = '';
    bindExamButtons();
    bindWeakPointButtons();
    loadMyExamResults();
  };
  tryInit(10);
}

function bindExamButtons() {
  // subject options 投入
  const subjSel = document.getElementById('exSubject');
  if (subjSel && !subjSel.options.length) {
    subjSel.innerHTML = '<option value="">-- 選択 --</option>' + SP_SUBJECTS.map(s => `<option value="${s}">${s}</option>`).join('');
  }
  const toggle = document.getElementById('exToggleFormBtn');
  const cancel = document.getElementById('exFormCancelBtn');
  const submit = document.getElementById('exSubmitBtn');
  if (toggle && !toggle._exBound) {
    toggle.addEventListener('click', () => {
      const w = document.getElementById('exFormWrap');
      const isOpen = w.style.display !== 'none';
      w.style.display = isOpen ? 'none' : '';
      if (!isOpen && !document.getElementById('exDate').value) {
        document.getElementById('exDate').value = _slJstDate(0);
      }
    });
    toggle._exBound = true;
  }
  if (cancel && !cancel._exBound) {
    cancel.addEventListener('click', () => { document.getElementById('exFormWrap').style.display = 'none'; });
    cancel._exBound = true;
  }
  if (submit && !submit._exBound) {
    submit.addEventListener('click', submitExamResult);
    submit._exBound = true;
  }
  // 📷 模試写真スキャン
  const scanBtn = document.getElementById('exScanPhotoBtn');
  const scanInput = document.getElementById('exScanPhotoInput');
  const scanClose = document.getElementById('exScanCloseBtn');
  const scanSelectAll = document.getElementById('exScanSelectAllBtn');
  const scanSave = document.getElementById('exScanSaveBtn');
  if (scanBtn && !scanBtn._exBound) {
    scanBtn.addEventListener('click', () => scanInput && scanInput.click());
    scanBtn._exBound = true;
  }
  if (scanInput && !scanInput._exBound) {
    scanInput.addEventListener('change', handleExamPhoto);
    scanInput._exBound = true;
  }
  if (scanClose && !scanClose._exBound) {
    scanClose.addEventListener('click', () => { document.getElementById('exScanPreview').style.display = 'none'; });
    scanClose._exBound = true;
  }
  if (scanSelectAll && !scanSelectAll._exBound) {
    scanSelectAll.addEventListener('click', () => {
      const boxes = document.querySelectorAll('#exScanSubjects .ex-scan-cb');
      const allChecked = Array.from(boxes).every(b => b.checked);
      boxes.forEach(b => { b.checked = !allChecked; });
      scanSelectAll.textContent = allChecked ? '☑ 全件選択' : '☐ 全件解除';
    });
    scanSelectAll._exBound = true;
  }
  if (scanSave && !scanSave._exBound) {
    scanSave.addEventListener('click', saveDetectedExams);
    scanSave._exBound = true;
  }
}

// 📷 模試スキャン: 画像 or PDF を Claude Vision で全科目一括抽出
async function handleExamPhoto(e) {
  const file = e.target.files && e.target.files[0];
  if (!file) return;
  const scanBtn = document.getElementById('exScanPhotoBtn');
  const preview = document.getElementById('exScanPreview');
  const commonEl = document.getElementById('exScanCommon');
  const subjectsEl = document.getElementById('exScanSubjects');
  const msg = document.getElementById('exScanMsg');
  const isPdf = file.type === 'application/pdf' || /\.pdf$/i.test(file.name || '');
  if (preview) preview.style.display = '';
  if (commonEl) commonEl.textContent = '';
  if (subjectsEl) subjectsEl.innerHTML = `<div style="text-align:center; color:#c4b5fd; padding:1rem;">🔍 ${isPdf ? 'PDF を画像化中...' : 'AI が読み取り中...'} (10-30秒)</div>`;
  if (msg) { msg.textContent = ''; msg.style.color = '#a1a1aa'; }
  if (scanBtn) { scanBtn.disabled = true; scanBtn.textContent = '⏳ スキャン中...'; }
  try {
    let imageParts;
    if (isPdf) {
      // PDF: 最初の3ページを画像化して複数 image part として送信
      imageParts = await _pdfToImageParts(file, { maxPages: 3, scale: 2.0, quality: 0.82, maxSide: 1400 });
      if (subjectsEl) subjectsEl.innerHTML = `<div style="text-align:center; color:#c4b5fd; padding:1rem;">🔍 ${imageParts.length}ページ抽出 → AI が解析中... (15-30秒)</div>`;
    } else {
      const dataUrl = await _compressImage(file, 1280, 0.82);
      const base64 = dataUrl.split(',')[1];
      const mime = dataUrl.match(/data:(image\/[^;]+);/)[1];
      imageParts = [{ type: 'image', source: { type: 'base64', media_type: mime, data: base64 } }];
    }
    const token = (window.AuthGuard && window.AuthGuard.getToken()) || localStorage.getItem('ai_juku_session_token');
    const student = (window.AuthGuard && window.AuthGuard.getStudent && window.AuthGuard.getStudent()) || {};
    const sid = student.id || 'guest';
    const allowedSubjects = '英語/数学/国語/現代文/古文/漢文/理科/物理/化学/生物/地学/社会/日本史/世界史/地理/倫理/政経/情報/小論文/面接対策/その他';
    const promptText = `画像は日本の大学受験模試 (河合塾・駿台・東進・ベネッセ・進研模試等) の成績表です。\n読み取れた全科目を抽出し、純粋な JSON のみで返してください (前置きやコードフェンス禁止):\n{\n  "exam_name": "模試名 (例: 河合塾 第1回全統共通テスト模試)",\n  "exam_date": "受験日 YYYY-MM-DD (完全な日付が判読不能なら null。月だけ見えても推測せず null)",\n  "target_university": "成績表に記載された志望校 (1校。なければ null)",\n  "subjects": [\n    {\n      "subject": "次のいずれか1つに必ず正規化: ${allowedSubjects}",\n      "score": 数値 or null,\n      "max_score": 数値 or null,\n      "deviation": 数値 or null,\n      "judgement": "A|B|C|D|E or null",\n      "weak_areas": "苦手分野・大問別の名前 (画像の表に「リスニング」「長文読解」「文法」等の項目別得点が見えれば項目名を列挙)。なければ null"\n    }\n  ],\n  "confidence": "high|mid|low"\n}\n科目正規化ルール:\n- 数学IA/IIB/III/数IA/数IIB等 → "数学"\n- 物理基礎/化学基礎/生物基礎 → "物理"/"化学"/"生物" (基礎を除く)\n- 共通テスト英語のリーディング/リスニング両方が見えても合算せず、配点の大きい方を「英語」として1件にまとめる (合算した score を返す)\n- 古文+漢文が「古典」と1項目で表記されていれば "国語" にまとめる (古文/漢文 別欄なら個別に)\n- 倫理政経/倫政 → "社会"\n\n厳格ルール (絶対遵守):\n- 判読不能な数値・日付は必ず null。決して推測しない\n- score ≤ max_score を満たすこと。違反する組合せは両方 null にする\n- ぼやけ・反射・手書き訂正で読みにくい値は null + confidence: "low"\n- 返答は完全に有効な JSON のみ。説明文・前置き・後置き・\`\`\` フェンス禁止`;
    const res = await fetch(SL_API_BASE + '/api/ai/call', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + (token || '') },
      body: JSON.stringify({
        student_id: sid,
        model: 'claude-sonnet-4-6',
        max_tokens: 1500,
        kind: isPdf ? 'exam_pdf_scan' : 'exam_photo_scan',
        system: 'あなたは日本の大学受験模試成績表から数値データを高精度に抽出する OCR 専門家です。返答は必ず完全に有効な純粋 JSON のみで、コードフェンスや説明文は一切含めません。',
        messages: [{
          role: 'user',
          content: [
            { type: 'text', text: promptText + (isPdf && imageParts.length > 1 ? `\n\n【重要・複数ページ統合ルール】${imageParts.length}ページの画像を提供しています。同一の模試として処理し、以下を厳守:\n1. 同一科目の重複排除: 複数ページで同じ科目が出現した場合、より詳細な値 (大問別 breakdown が見えるページ) を優先し、subjects 配列に同一科目を2回以上含めない\n2. 空白/表紙ページをスキップ: 数値データのないページ (校章のみ、白紙) は無視\n3. 大問別表は科目に紐付ける: 表が「英語」のセクションに配置されているなら weak_areas は英語の subjects エントリにのみ記載\n4. 配置の典型例 - ページ1: 模試名/総合点 / ページ2-N: 科目別詳細。exam_name と exam_date は最初に見つけた値で固定し、後続ページで上書きしない` : '') },
            ...imageParts
          ]
        }],
      }),
    });
    if (!res.ok) {
      const errTxt = await res.text();
      throw new Error(`HTTP ${res.status}: ${errTxt.slice(0, 120)}`);
    }
    const data = await res.json();
    const txt = (data.content || []).map(c => c.text || '').join('').trim();
    const jsonStr = txt.replace(/^```(?:json)?\s*|\s*```$/g, '');
    let parsed;
    try { parsed = JSON.parse(jsonStr); }
    catch { const m = jsonStr.match(/\{[\s\S]*\}/); if (m) parsed = JSON.parse(m[0]); else throw new Error('JSON 解析失敗'); }
    const subjects = Array.isArray(parsed.subjects) ? parsed.subjects : [];
    if (!subjects.length) {
      if (subjectsEl) subjectsEl.innerHTML = `
        <div style="color:#fca5a5; padding:0.7rem; margin-bottom:0.5rem;">❌ 科目を読み取れませんでした。画像が不鮮明か、模試結果以外の写真の可能性があります。</div>
        <button type="button" id="exScanFallbackBtn" style="width:100%; padding:0.55rem; background:rgba(16,185,129,0.15); border:1px solid rgba(16,185,129,0.4); border-radius:8px; color:#86efac; font-weight:700; cursor:pointer; font-size:0.85rem;">＋ 手入力フォームを開く</button>`;
      const fallback = document.getElementById('exScanFallbackBtn');
      if (fallback) fallback.addEventListener('click', () => {
        document.getElementById('exScanPreview').style.display = 'none';
        document.getElementById('exFormWrap').style.display = '';
        if (!document.getElementById('exDate').value) document.getElementById('exDate').value = _slJstDate(0);
        const nameEl = document.getElementById('exName'); if (nameEl) nameEl.focus();
      });
      return;
    }
    // common 情報を表示
    const conf = parsed.confidence || 'mid';
    const confLabel = { high: '✅ 高精度', mid: '👍 確からしい', low: '⚠️ 低精度・要確認' }[conf] || '';
    const cleanDate = (parsed.exam_date && /^\d{4}-\d{2}-\d{2}$/.test(parsed.exam_date)) ? parsed.exam_date : '';
    const cleanName = parsed.exam_name || '';
    const cleanUni = parsed.target_university || '';
    const fallbackDate = _slJstDate(0);
    if (commonEl) {
      commonEl.innerHTML = `
        <div style="background:rgba(0,0,0,0.3); padding:0.6rem 0.8rem; border-radius:8px; margin-bottom:0.4rem;">
          <div style="font-size:0.74rem; color:#71717a; margin-bottom:0.4rem;">${confLabel} ${subjects.length}科目検出</div>
          <div style="display:grid; grid-template-columns:auto 1fr; gap:0.3rem 0.6rem; font-size:0.82rem;">
            <span style="color:#a1a1aa;">📋 模試名:</span> <input type="text" id="exScanCommonName" value="${escapeHtml(cleanName)}" maxlength="100" style="background:rgba(0,0,0,0.4); border:1px solid rgba(255,255,255,0.15); border-radius:4px; color:#fff; padding:0.3rem 0.5rem; font-size:0.82rem;">
            <span style="color:#a1a1aa;">📅 受験日:</span> <input type="date" id="exScanCommonDate" value="${escapeHtml(cleanDate || fallbackDate)}" style="background:rgba(0,0,0,0.4); border:1px solid rgba(255,255,255,0.15); border-radius:4px; color:#fff; padding:0.3rem 0.5rem; font-size:0.82rem;">
            <span style="color:#a1a1aa;">🎯 志望校:</span> <input type="text" id="exScanCommonUni" value="${escapeHtml(cleanUni)}" maxlength="100" placeholder="(任意)" style="background:rgba(0,0,0,0.4); border:1px solid rgba(255,255,255,0.15); border-radius:4px; color:#fff; padding:0.3rem 0.5rem; font-size:0.82rem;">
          </div>
        </div>`;
    }
    // subjects rendering
    if (subjectsEl) {
      subjectsEl.innerHTML = subjects.map((s, i) => {
        const subjVal = SP_SUBJECTS.includes(s.subject) ? s.subject : 'その他';
        const subjOpts = SP_SUBJECTS.map(opt => `<option value="${opt}"${opt === subjVal ? ' selected' : ''}>${opt}</option>`).join('');
        const judgeOpts = ['', 'A', 'B', 'C', 'D', 'E'].map(j => `<option value="${j}"${(s.judgement || '') === j ? ' selected' : ''}>${j ? j + '判定' : '-- 任意 --'}</option>`).join('');
        const score = s.score !== null && s.score !== undefined ? s.score : '';
        const maxScore = s.max_score !== null && s.max_score !== undefined ? s.max_score : '';
        const dev = s.deviation !== null && s.deviation !== undefined ? s.deviation : '';
        const weakAreas = s.weak_areas || '';
        return `
          <div style="background:rgba(255,255,255,0.04); border:1px solid rgba(167,139,250,0.25); border-radius:8px; padding:0.6rem; margin-bottom:0.4rem;">
            <label style="display:flex; align-items:center; gap:0.5rem; cursor:pointer; margin-bottom:0.4rem;">
              <input type="checkbox" class="ex-scan-cb" data-idx="${i}" checked style="width:1.1em; height:1.1em; cursor:pointer;">
              <span style="font-weight:700; color:#e4e4e7; font-size:0.88rem;">この科目を保存</span>
            </label>
            <div class="ex-scan-grid-4" style="display:grid; grid-template-columns:repeat(4, 1fr); gap:0.4rem;">
              <div><label style="display:block; font-size:0.68rem; color:#a1a1aa; margin-bottom:0.15rem;">科目</label><select class="ex-scan-subject" data-idx="${i}" style="width:100%; padding:0.4rem; background:rgba(0,0,0,0.4); border:1px solid rgba(255,255,255,0.15); border-radius:4px; color:#fff; font-size:0.82rem;">${subjOpts}</select></div>
              <div><label style="display:block; font-size:0.68rem; color:#a1a1aa; margin-bottom:0.15rem;">得点</label><input type="number" class="ex-scan-score" data-idx="${i}" min="0" max="1000" value="${score}" style="width:100%; padding:0.4rem; background:rgba(0,0,0,0.4); border:1px solid rgba(255,255,255,0.15); border-radius:4px; color:#fff; font-size:0.82rem;"></div>
              <div><label style="display:block; font-size:0.68rem; color:#a1a1aa; margin-bottom:0.15rem;">満点</label><input type="number" class="ex-scan-maxscore" data-idx="${i}" min="1" max="1000" value="${maxScore}" style="width:100%; padding:0.4rem; background:rgba(0,0,0,0.4); border:1px solid rgba(255,255,255,0.15); border-radius:4px; color:#fff; font-size:0.82rem;"></div>
              <div><label style="display:block; font-size:0.68rem; color:#a1a1aa; margin-bottom:0.15rem;">偏差値</label><input type="number" step="0.1" class="ex-scan-dev" data-idx="${i}" min="10" max="100" value="${dev}" style="width:100%; padding:0.4rem; background:rgba(0,0,0,0.4); border:1px solid rgba(255,255,255,0.15); border-radius:4px; color:#fff; font-size:0.82rem;"></div>
            </div>
            <div class="ex-scan-grid-2" style="display:grid; grid-template-columns:1fr 2fr; gap:0.4rem; margin-top:0.4rem;">
              <div><label style="display:block; font-size:0.68rem; color:#a1a1aa; margin-bottom:0.15rem;">判定</label><select class="ex-scan-judge" data-idx="${i}" style="width:100%; padding:0.4rem; background:rgba(0,0,0,0.4); border:1px solid rgba(255,255,255,0.15); border-radius:4px; color:#fff; font-size:0.82rem;">${judgeOpts}</select></div>
              <div><label style="display:block; font-size:0.68rem; color:#a1a1aa; margin-bottom:0.15rem;">弱点メモ (AI抽出・編集可)</label><input type="text" class="ex-scan-note" data-idx="${i}" maxlength="500" value="${escapeHtml(weakAreas)}" placeholder="例: 長文読解、ベクトル" style="width:100%; padding:0.4rem; background:rgba(0,0,0,0.4); border:1px solid rgba(255,255,255,0.15); border-radius:4px; color:#fff; font-size:0.82rem;"></div>
            </div>
          </div>`;
      }).join('');
    }
  } catch (err) {
    console.error('exam photo scan failed:', err);
    if (subjectsEl) subjectsEl.innerHTML = `<div style="color:#fca5a5; padding:0.7rem;">❌ ${escapeHtml(err.message || '読取失敗')}</div>`;
  } finally {
    if (scanBtn) { scanBtn.disabled = false; scanBtn.textContent = '📷 模試写真をスキャン'; }
    if (e.target) e.target.value = '';
  }
}

async function saveDetectedExams() {
  const saveBtn = document.getElementById('exScanSaveBtn');
  const msg = document.getElementById('exScanMsg');
  const subjectsEl = document.getElementById('exScanSubjects');
  if (!saveBtn || saveBtn.disabled || !subjectsEl) return;
  const nameEl = document.getElementById('exScanCommonName');
  const dateEl = document.getElementById('exScanCommonDate');
  const uniEl = document.getElementById('exScanCommonUni');
  const examName = (nameEl && nameEl.value || '').trim();
  const examDate = (dateEl && dateEl.value || '').trim();
  const targetUni = (uniEl && uniEl.value || '').trim();
  if (!examName) {
    msg.style.color = '#fca5a5'; msg.textContent = '模試名を入力してください (赤枠の欄)';
    if (nameEl) { nameEl.style.border = '1px solid #fca5a5'; nameEl.focus(); nameEl.scrollIntoView({ behavior: 'smooth', block: 'center' }); }
    return;
  }
  if (!examDate) {
    msg.style.color = '#fca5a5'; msg.textContent = '受験日を入力してください (赤枠の欄)';
    if (dateEl) { dateEl.style.border = '1px solid #fca5a5'; dateEl.focus(); dateEl.scrollIntoView({ behavior: 'smooth', block: 'center' }); }
    return;
  }
  if (nameEl) nameEl.style.border = '1px solid rgba(255,255,255,0.15)';
  if (dateEl) dateEl.style.border = '1px solid rgba(255,255,255,0.15)';
  const checks = subjectsEl.querySelectorAll('.ex-scan-cb');
  const targets = [];
  checks.forEach(cb => {
    if (!cb.checked) return;
    const idx = cb.getAttribute('data-idx');
    const subject = subjectsEl.querySelector(`.ex-scan-subject[data-idx="${idx}"]`).value;
    const score = subjectsEl.querySelector(`.ex-scan-score[data-idx="${idx}"]`).value;
    const maxScore = subjectsEl.querySelector(`.ex-scan-maxscore[data-idx="${idx}"]`).value;
    const dev = subjectsEl.querySelector(`.ex-scan-dev[data-idx="${idx}"]`).value;
    const judge = subjectsEl.querySelector(`.ex-scan-judge[data-idx="${idx}"]`).value;
    const note = subjectsEl.querySelector(`.ex-scan-note[data-idx="${idx}"]`).value.trim();
    targets.push({ subject, score, maxScore, dev, judge, note });
  });
  if (!targets.length) { msg.style.color = '#fca5a5'; msg.textContent = '保存する科目を1つ以上選択してください'; return; }
  saveBtn.disabled = true; saveBtn.textContent = '保存中...';
  msg.style.color = '#a78bfa'; msg.textContent = `0 / ${targets.length} 件保存中...`;
  let success = 0;
  const errors = [];
  for (let i = 0; i < targets.length; i++) {
    const t = targets[i];
    try {
      await slApiFetch('/api/exam-results', {
        method: 'POST',
        body: JSON.stringify({
          exam_name: examName,
          exam_date: examDate,
          subject: t.subject,
          score: t.score ? parseInt(t.score, 10) : undefined,
          max_score: t.maxScore ? parseInt(t.maxScore, 10) : undefined,
          deviation: t.dev ? parseFloat(t.dev) : undefined,
          judgement: t.judge || undefined,
          target_university: targetUni || undefined,
          note: t.note || undefined,
        }),
      });
      success++;
      msg.textContent = `${success} / ${targets.length} 件保存中...`;
    } catch (e) {
      errors.push(`${t.subject}: ${e.message || '失敗'}`);
    }
  }
  if (errors.length === 0) {
    const savedSubjects = targets.map(t => t.subject).join(', ');
    msg.style.color = '#86efac'; msg.textContent = `✅ ${success} 件保存完了: ${savedSubjects}`;
    await loadMyExamResults();
    triggerAutoGapAnalysis();
    setTimeout(() => { document.getElementById('exScanPreview').style.display = 'none'; }, 2800);
  } else {
    msg.style.color = '#fca5a5'; msg.innerHTML = `⚠️ ${success}件成功 / ${errors.length}件失敗<br>${errors.map(e => escapeHtml(e)).join('<br>')}`;
    if (success > 0) await loadMyExamResults();
  }
  saveBtn.disabled = false; saveBtn.textContent = '💾 選択した科目を保存';
}

async function submitExamResult() {
  const btn = document.getElementById('exSubmitBtn');
  const msg = document.getElementById('exFormMsg');
  if (!btn || btn.disabled) return;
  const name = document.getElementById('exName').value.trim();
  const date = document.getElementById('exDate').value;
  const subject = document.getElementById('exSubject').value;
  const score = document.getElementById('exScore').value;
  const maxScore = document.getElementById('exMaxScore').value;
  const dev = document.getElementById('exDeviation').value;
  const judgement = document.getElementById('exJudgement').value;
  const targetUni = document.getElementById('exTargetUni').value.trim();
  const note = document.getElementById('exNote').value.trim();
  if (!name || !date || !subject) { msg.style.color = '#fca5a5'; msg.textContent = '模試名・受験日・科目は必須'; return; }
  btn.disabled = true; btn.textContent = '保存中...';
  try {
    await slApiFetch('/api/exam-results', {
      method: 'POST',
      body: JSON.stringify({
        exam_name: name, exam_date: date, subject,
        score: score ? parseInt(score, 10) : undefined,
        max_score: maxScore ? parseInt(maxScore, 10) : undefined,
        deviation: dev ? parseFloat(dev) : undefined,
        judgement: judgement || undefined,
        target_university: targetUni || undefined,
        note: note || undefined,
      }),
    });
    msg.style.color = '#86efac'; msg.textContent = '✅ 模試結果を保存しました';
    // clear form (model+date は保持・他クリア)
    ['exScore', 'exMaxScore', 'exDeviation', 'exNote'].forEach(id => { const el = document.getElementById(id); if (el) el.value = ''; });
    document.getElementById('exJudgement').value = '';
    await loadMyExamResults();
    // Phase 4.7: アクティブカリキュラムがあれば自動 gap-analyze
    triggerAutoGapAnalysis();
  } catch (e) {
    msg.style.color = '#fca5a5'; msg.textContent = '❌ ' + (e.message || '保存失敗');
  } finally {
    btn.disabled = false; btn.textContent = '📊 結果を保存';
  }
}

async function loadMyExamResults() {
  const list = document.getElementById('exList');
  const summaryEl = document.getElementById('exLatestSummary');
  if (!list) return;
  try {
    const data = await slApiFetch('/api/exam-results/me?limit=200');
    const ext = data.external || [];
    const internal = data.internal || [];
    const all = [...ext, ...internal].sort((a, b) => (b.exam_date || '').localeCompare(a.exam_date || ''));
    // 直近サマリ
    if (data.latest_summary) {
      const ls = data.latest_summary;
      const avg = ls.average_deviation;
      const avgColor = avg >= 65 ? '#86efac' : avg >= 55 ? '#fbbf24' : '#fca5a5';
      summaryEl.innerHTML = `
        <div style="background:rgba(0,0,0,0.3); border-left:4px solid ${avgColor}; border-radius:8px; padding:0.85rem; margin-bottom:0.5rem;">
          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.4rem;">
            <div style="font-size:0.85rem; color:#86efac; font-weight:700;">📊 直近模試 (${escapeHtml(ls.exam_date)}) 平均偏差値: <span style="color:${avgColor}; font-size:1.2rem;">${avg}</span></div>
            <div style="display:flex; gap:0.3rem; flex-wrap:wrap;">
              ${ls.subjects.map(s => {
                const c = s.deviation >= 65 ? '#86efac' : s.deviation >= 55 ? '#fbbf24' : '#fca5a5';
                const jd = s.judgement ? ` <span style="background:rgba(255,255,255,0.1); padding:0 0.3rem; border-radius:3px;">${s.judgement}</span>` : '';
                return `<span style="background:rgba(255,255,255,0.05); color:${c}; padding:0.2rem 0.5rem; border-radius:6px; font-size:0.78rem;">${escapeHtml(s.subject)}: ${s.deviation}${jd}</span>`;
              }).join('')}
            </div>
          </div>
        </div>`;
    } else {
      summaryEl.innerHTML = '';
    }
    // 偏差値推移グラフ
    renderExamTrendChart(data.by_subject_trend || {});
    // 一覧
    if (!all.length) {
      list.innerHTML = '<div style="text-align:center; color:#71717a; padding:1rem;">📊 まだ模試結果がありません。「＋ 模試結果を追加」から登録してみよう</div>';
      return;
    }
    list.innerHTML = `
      <div style="font-size:0.78rem; color:#a1a1aa; margin-bottom:0.4rem;">📋 模試履歴 (外部 ${ext.length} 件 / 内蔵 ${internal.length} 件)</div>
      ${all.slice(0, 30).map(r => {
        const isInternal = r.source === 'internal';
        const devColor = r.deviation >= 65 ? '#86efac' : r.deviation >= 55 ? '#fbbf24' : (r.deviation ? '#fca5a5' : '#71717a');
        const sourceTag = isInternal ? '<span style="background:rgba(167,139,250,0.2); color:#c4b5fd; padding:0.1rem 0.4rem; border-radius:4px; font-size:0.7rem;">🤖 AI模試</span>' : '<span style="background:rgba(16,185,129,0.2); color:#86efac; padding:0.1rem 0.4rem; border-radius:4px; font-size:0.7rem;">📋 外部</span>';
        const delBtn = isInternal ? '' : `<button data-id="${r.id}" class="ex-del-btn" style="background:none; border:0; color:#71717a; cursor:pointer; font-size:0.85rem;">🗑</button>`;
        return `
          <div style="background:rgba(255,255,255,0.04); border-radius:8px; padding:0.7rem; margin-bottom:0.4rem;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.3rem; flex-wrap:wrap; gap:0.3rem;">
              <div style="font-weight:700; color:#e4e4e7; font-size:0.88rem;">${sourceTag} ${escapeHtml(r.exam_name)}</div>
              <div style="font-size:0.72rem; color:#71717a;">${escapeHtml(r.exam_date || '')}</div>
            </div>
            <div style="display:flex; gap:0.5rem; flex-wrap:wrap; font-size:0.78rem;">
              <span style="color:#c7d2fe;">科目: ${escapeHtml(r.subject)}</span>
              ${r.deviation ? `<span style="color:${devColor}; font-weight:700;">偏差値 ${r.deviation}</span>` : ''}
              ${r.score !== null && r.score !== undefined ? `<span style="color:#a1a1aa;">${r.score}${r.max_score ? '/' + r.max_score : ''}点</span>` : ''}
              ${r.judgement ? `<span style="color:#fbbf24;">判定 ${r.judgement}</span>` : ''}
              ${r.target_university ? `<span style="color:#a1a1aa;">→ ${escapeHtml(r.target_university)}</span>` : ''}
            </div>
            ${r.note ? `<div style="font-size:0.78rem; color:#d4d4d8; margin-top:0.3rem;">${escapeHtml(r.note)}</div>` : ''}
            <div style="text-align:right; margin-top:0.2rem;">${delBtn}</div>
          </div>`;
      }).join('')}`;
    list.querySelectorAll('.ex-del-btn').forEach(b => b.addEventListener('click', () => deleteExamResult(b.getAttribute('data-id'))));
  } catch (e) {
    console.error('loadMyExamResults failed:', e);
    list.innerHTML = `<div style="text-align:center; color:#fca5a5; padding:1rem;">⚠️ 読み込み失敗 (${escapeHtml(e.message || '')})</div>`;
  }
}

function renderExamTrendChart(trendBySubj) {
  const canvas = document.getElementById('exTrendChart');
  const wrap = document.getElementById('exTrendWrap');
  if (!canvas || !wrap || !window.Chart) return;
  const subjects = Object.keys(trendBySubj);
  if (!subjects.length) {
    wrap.style.display = 'none';
    return;
  }
  wrap.style.display = '';
  // 全日付を集めて時系列順にソート
  const allDates = new Set();
  subjects.forEach(s => trendBySubj[s].forEach(p => allDates.add(p.date)));
  const labels = Array.from(allDates).sort();
  const palette = ['#6366f1', '#10b981', '#ec4899', '#f59e0b', '#8b5cf6', '#06b6d4', '#fbbf24', '#fb7185'];
  const datasets = subjects.map((s, i) => ({
    label: s,
    data: labels.map(d => {
      const point = trendBySubj[s].find(p => p.date === d);
      return point ? point.deviation : null;
    }),
    borderColor: palette[i % palette.length],
    backgroundColor: palette[i % palette.length] + '33',
    spanGaps: true,
    tension: 0.2,
  }));
  if (_exTrendChart) _exTrendChart.destroy();
  _exTrendChart = new Chart(canvas, {
    type: 'line',
    data: { labels, datasets },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { labels: { color: '#a1a1aa', font: { size: 10 } } } },
      scales: {
        x: { ticks: { color: '#a1a1aa', font: { size: 9 } }, grid: { color: 'rgba(255,255,255,0.05)' } },
        y: { ticks: { color: '#a1a1aa' }, grid: { color: 'rgba(255,255,255,0.05)' }, suggestedMin: 35, suggestedMax: 75 },
      },
    },
  });
}

async function deleteExamResult(id) {
  if (!confirm('この模試結果を削除しますか?')) return;
  try {
    await slApiFetch(`/api/exam-results/${encodeURIComponent(id)}`, { method: 'DELETE' });
    await loadMyExamResults();
  } catch (e) {
    alert('削除失敗: ' + (e.message || ''));
  }
}


// ==========================================================================
// 🎯 AI 弱点プリント生成 (Phase 4.6)
// ==========================================================================
function bindWeakPointButtons() {
  // subject options 投入 + 弱点 hint
  const sel = document.getElementById('wpSubject');
  if (sel && !sel.options.length) {
    sel.innerHTML = '<option value="">-- 選択 --</option>' + SP_SUBJECTS.map(s => `<option value="${s}">${s}</option>`).join('');
    sel.addEventListener('change', updateWpSubjectHint);
  }
  const toggle = document.getElementById('wpToggleBtn');
  const cancel = document.getElementById('wpCancelBtn');
  const submit = document.getElementById('wpSubmitBtn');
  if (toggle && !toggle._wpBound) {
    toggle.addEventListener('click', async () => {
      const w = document.getElementById('wpFormWrap');
      const isOpen = w.style.display !== 'none';
      w.style.display = isOpen ? 'none' : '';
      if (!isOpen) {
        // 模試結果から弱点科目を auto-suggest
        await autoSuggestWeakSubject();
      }
    });
    toggle._wpBound = true;
  }
  if (cancel && !cancel._wpBound) {
    cancel.addEventListener('click', () => { document.getElementById('wpFormWrap').style.display = 'none'; });
    cancel._wpBound = true;
  }
  if (submit && !submit._wpBound) {
    submit.addEventListener('click', generateWeakPointWorksheet);
    submit._wpBound = true;
  }
}

async function autoSuggestWeakSubject() {
  const sel = document.getElementById('wpSubject');
  const hint = document.getElementById('wpSubjectHint');
  if (!sel || !hint) return;
  try {
    const data = await slApiFetch('/api/exam-results/me?limit=50');
    const trend = data.by_subject_trend || {};
    // 各科目の最新偏差値を収集 → 偏差値が一番低いものを suggest
    const latests = [];
    Object.keys(trend).forEach(s => {
      const arr = trend[s] || [];
      if (arr.length && arr[0].deviation != null) {
        latests.push({ subject: s, deviation: arr[0].deviation });
      }
    });
    if (!latests.length) {
      hint.textContent = '💡 模試結果がまだありません。「📊 模試結果を追加」から登録すると、AI が弱点を自動検出します。';
      hint.style.color = '#a1a1aa';
      return;
    }
    latests.sort((a, b) => a.deviation - b.deviation);
    const weakest = latests[0];
    if (sel.value === '') sel.value = weakest.subject;
    hint.textContent = `💡 直近模試で偏差値が低い順: ${latests.slice(0, 3).map(x => `${x.subject}(${x.deviation})`).join(' / ')} → 推奨「${weakest.subject}」を自動選択`;
    hint.style.color = '#86efac';
  } catch (e) {
    hint.textContent = '';
  }
}

function updateWpSubjectHint() {
  // 個別 hint 更新 (科目変更時)
  const hint = document.getElementById('wpSubjectHint');
  if (hint) hint.textContent = '';
}

async function generateWeakPointWorksheet() {
  const btn = document.getElementById('wpSubmitBtn');
  const msg = document.getElementById('wpMsg');
  const result = document.getElementById('wpResult');
  if (!btn || btn.disabled) return;
  const subject = document.getElementById('wpSubject').value;
  const topic = document.getElementById('wpTopic').value.trim();
  const num = parseInt(document.getElementById('wpNum').value, 10) || 8;
  const uni = document.getElementById('wpUni').value.trim();
  if (!subject) { msg.style.color = '#fca5a5'; msg.textContent = '科目を選択してください'; return; }
  if (num < 3 || num > 15) { msg.style.color = '#fca5a5'; msg.textContent = '問題数は 3-15 で指定'; return; }

  btn.disabled = true; btn.textContent = '🤖 AI が問題作成中... (15-30秒)';
  msg.style.color = '#fbbf24'; msg.textContent = '🎯 弱点を分析して問題を生成しています...';
  result.innerHTML = '';
  try {
    const data = await slApiFetch('/api/weak-points/generate-worksheet', {
      method: 'POST',
      body: JSON.stringify({
        subject, topic: topic || undefined, num_problems: num, target_university: uni || undefined,
      }),
    });
    msg.style.color = '#86efac'; msg.textContent = `✅ 弱点プリントを生成しました (${data.problems.length} 問)`;
    result.innerHTML = renderWorksheet(data);
    // 印刷ボタンと解答 toggle
    const printBtn = document.getElementById('wpPrintBtn');
    const ansToggle = document.getElementById('wpAnsToggleBtn');
    if (printBtn) printBtn.addEventListener('click', () => printWorksheet(data));
    if (ansToggle) ansToggle.addEventListener('click', () => {
      document.querySelectorAll('.wp-ans-block').forEach(el => {
        el.style.display = el.style.display === 'none' ? '' : 'none';
      });
      ansToggle.textContent = ansToggle.textContent.includes('表示') ? '🙈 解答を隠す' : '👁 解答を表示';
    });
  } catch (e) {
    msg.style.color = '#fca5a5'; msg.textContent = '❌ ' + (e.message || '生成失敗');
  } finally {
    btn.disabled = false; btn.textContent = '✨ 弱点プリントを生成 (15-30秒)';
  }
}

function renderWorksheet(d) {
  const probsHtml = (d.problems || []).map(p => {
    const diffColor = { '易': '#86efac', '標準': '#fbbf24', '応用': '#f97316', '発展': '#fca5a5' }[p.difficulty] || '#a1a1aa';
    return `
      <div style="background:rgba(255,255,255,0.04); border-radius:8px; padding:0.85rem; margin-bottom:0.6rem; page-break-inside:avoid;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.4rem;">
          <div style="font-weight:700; color:#fbbf24;">問題 ${p.no}</div>
          <span style="background:rgba(255,255,255,0.1); color:${diffColor}; padding:0.1rem 0.5rem; border-radius:4px; font-size:0.72rem; font-weight:700;">${escapeHtml(p.difficulty)}</span>
        </div>
        <div style="color:#e4e4e7; font-size:0.92rem; white-space:pre-wrap; margin-bottom:0.5rem; line-height:1.6;">${escapeHtml(p.question)}</div>
        <div class="wp-ans-block" style="background:rgba(16,185,129,0.08); border-left:3px solid #10b981; padding:0.5rem 0.75rem; border-radius:6px; margin-top:0.4rem;">
          <div style="font-weight:700; color:#86efac; font-size:0.78rem; margin-bottom:0.2rem;">✅ 解答</div>
          <div style="color:#e4e4e7; font-size:0.85rem; white-space:pre-wrap;">${escapeHtml(p.answer)}</div>
        </div>
        <div class="wp-ans-block" style="background:rgba(99,102,241,0.08); border-left:3px solid #6366f1; padding:0.5rem 0.75rem; border-radius:6px; margin-top:0.3rem;">
          <div style="font-weight:700; color:#c7d2fe; font-size:0.78rem; margin-bottom:0.2rem;">💡 解説</div>
          <div style="color:#d4d4d8; font-size:0.85rem; white-space:pre-wrap; line-height:1.6;">${escapeHtml(p.explanation)}</div>
        </div>
      </div>`;
  }).join('');
  const lecturesHtml = (d.sapuri_lectures || []).map((l, i) => `
    <div style="background:rgba(251,113,133,0.08); border-left:3px solid #fb7185; border-radius:6px; padding:0.6rem; margin-bottom:0.4rem;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.2rem;">
        <div style="font-weight:700; color:#fda4af; font-size:0.88rem;">${i + 1}. 📺 ${escapeHtml(l.title)}</div>
        <span style="background:rgba(251,113,133,0.2); color:#fda4af; padding:0.1rem 0.5rem; border-radius:4px; font-size:0.7rem; font-weight:700;">${escapeHtml(l.level)}</span>
      </div>
      <div style="color:#d4d4d8; font-size:0.78rem;">💡 ${escapeHtml(l.reason)}</div>
    </div>`).join('');
  return `
    <div style="background:rgba(0,0,0,0.3); border-radius:10px; padding:1rem;">
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.5rem; margin-bottom:0.7rem;">
        <div>
          <div style="font-size:0.92rem; color:#fbbf24; font-weight:800;">📋 ${escapeHtml(d.subject)} 弱点プリント</div>
          <div style="font-size:0.78rem; color:#a1a1aa; margin-top:0.2rem;">テーマ: ${escapeHtml(d.topic_used)}</div>
        </div>
        <div style="display:flex; gap:0.3rem;">
          <button id="wpAnsToggleBtn" type="button" style="background:rgba(99,102,241,0.2); color:#c7d2fe; border:0; padding:0.4rem 0.7rem; border-radius:6px; cursor:pointer; font-size:0.78rem;">🙈 解答を隠す</button>
          <button id="wpPrintBtn" type="button" style="background:linear-gradient(135deg,#10b981,#34d399); color:#fff; border:0; padding:0.4rem 0.8rem; border-radius:6px; cursor:pointer; font-size:0.78rem; font-weight:700;">🖨 印刷</button>
        </div>
      </div>
      ${d.weak_point_analysis ? `<div style="background:rgba(245,158,11,0.08); border-left:3px solid #f59e0b; padding:0.55rem 0.75rem; border-radius:6px; margin-bottom:0.7rem; font-size:0.85rem; color:#e4e4e7;">🎯 <strong style="color:#fbbf24;">弱点分析:</strong> ${escapeHtml(d.weak_point_analysis)}</div>` : ''}
      ${probsHtml}
      ${lecturesHtml ? `
        <div style="margin-top:1rem; padding-top:0.7rem; border-top:1px solid rgba(255,255,255,0.1);">
          <div style="font-size:0.88rem; color:#fda4af; font-weight:700; margin-bottom:0.4rem;">📺 補強推薦: スタサプ講義 (${d.sapuri_lectures.length} 件・易→難)</div>
          ${lecturesHtml}
        </div>` : ''}
    </div>`;
}

function printWorksheet(d) {
  const probsHtml = (d.problems || []).map(p => `
    <div style="page-break-inside:avoid; margin-bottom:1rem; border-bottom:1px solid #ccc; padding-bottom:0.7rem;">
      <h3 style="margin:0 0 0.3rem 0;">問題 ${p.no} <span style="font-size:0.7em; background:#eee; padding:1px 5px; border-radius:3px;">${p.difficulty}</span></h3>
      <div style="white-space:pre-wrap; line-height:1.6;">${escapeHtml(p.question)}</div>
      <div style="margin-top:0.5rem; padding:0.4rem; background:#f0fdf4;"><strong>解答:</strong> ${escapeHtml(p.answer)}</div>
      <div style="margin-top:0.3rem; padding:0.4rem; background:#eff6ff;"><strong>解説:</strong> ${escapeHtml(p.explanation)}</div>
    </div>`).join('');
  const lectHtml = (d.sapuri_lectures || []).map((l, i) => `
    <li style="margin-bottom:0.3rem;"><strong>${i + 1}. ${escapeHtml(l.title)}</strong> [${escapeHtml(l.level)}] - ${escapeHtml(l.reason)}</li>
  `).join('');
  const html = `<!DOCTYPE html><html><head><meta charset="UTF-8"><title>${escapeHtml(d.subject)} 弱点プリント</title>
    <style>body{font-family:'Hiragino Sans','Yu Gothic',sans-serif; padding:2rem; max-width:800px; margin:0 auto; line-height:1.6;} h1{border-bottom:2px solid #333;} h3{margin-top:1rem;} @media print { body{padding:1rem;} }</style>
    </head><body>
    <h1>📋 ${escapeHtml(d.subject)} 弱点プリント</h1>
    <p><strong>テーマ:</strong> ${escapeHtml(d.topic_used)}</p>
    ${d.weak_point_analysis ? `<div style="background:#fef3c7; padding:0.7rem; border-left:4px solid #f59e0b; margin:1rem 0;"><strong>🎯 弱点分析:</strong> ${escapeHtml(d.weak_point_analysis)}</div>` : ''}
    <hr>
    ${probsHtml}
    ${lectHtml ? `<h2>📺 補強推薦: スタサプ講義</h2><ul>${lectHtml}</ul>` : ''}
    </body></html>`;
  const w = window.open('', '_blank');
  if (!w) { alert('ポップアップがブロックされました'); return; }
  w.document.write(html);
  w.document.close();
  setTimeout(() => w.print(), 500);
}


// ==========================================================================
// 📊 ギャップ分析 (Phase 4.7) - 模試追加 → 自動カリキュラム修正提案
// ==========================================================================
async function triggerAutoGapAnalysis() {
  // _cuLastList に active カリキュラムがあるか確認 → なければ skip
  if (!_cuLastList || !_cuLastList.length) {
    // まだ load されていない場合は load してから判定
    try {
      const data = await slApiFetch('/api/curricula/me');
      _cuLastList = data.curricula || [];
    } catch { return; }
  }
  const active = (_cuLastList || []).find(c => c.status === 'active');
  if (!active) return;
  // 通知 + 分析開始
  try {
    showGapAnalysisModal('loading', { curriculum: active });
    const data = await slApiFetch(`/api/curricula/${encodeURIComponent(active.id)}/gap-analyze`, { method: 'POST' });
    showGapAnalysisModal('result', { curriculum: active, ...data });
  } catch (e) {
    console.error('gap analyze failed:', e);
    showGapAnalysisModal('error', { curriculum: active, error: e.message });
  }
}

function showGapAnalysisModal(state, ctx) {
  let modal = document.getElementById('gapAnalysisModal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'gapAnalysisModal';
    modal.style.cssText = 'position:fixed; inset:0; background:rgba(0,0,0,0.7); z-index:9999; display:flex; align-items:flex-start; justify-content:center; padding:2rem; overflow-y:auto;';
    modal.innerHTML = `
      <div style="background:#0f172a; border:1px solid rgba(167,139,250,0.4); border-radius:14px; padding:1.5rem; max-width:760px; width:100%;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
          <h3 style="margin:0; color:#c4b5fd;">📊 AI ギャップ分析 (志望校 vs 現状)</h3>
          <button id="gapModalClose" type="button" style="background:none; border:0; color:#a1a1aa; font-size:1.5rem; cursor:pointer;">×</button>
        </div>
        <div id="gapModalBody"></div>
      </div>`;
    document.body.appendChild(modal);
    modal.querySelector('#gapModalClose').addEventListener('click', () => modal.style.display = 'none');
    modal.addEventListener('click', e => { if (e.target === modal) modal.style.display = 'none'; });
    document.addEventListener('keydown', e => { if (e.key === 'Escape' && modal.style.display === 'flex') modal.style.display = 'none'; });
  }
  modal.style.display = 'flex';
  const body = modal.querySelector('#gapModalBody');

  if (state === 'loading') {
    body.innerHTML = `
      <div style="text-align:center; padding:2rem; color:#a1a1aa;">
        <div style="font-size:2.5rem; margin-bottom:0.5rem;">🤖</div>
        <div>AI が「${escapeHtml(ctx.curriculum.target_university || '志望校')}」までのギャップを分析中... (10-25秒)</div>
        <div style="font-size:0.8rem; color:#71717a; margin-top:0.5rem;">模試結果 + 現行カリキュラムを総合判断</div>
      </div>`;
    return;
  }
  if (state === 'error') {
    body.innerHTML = `<div style="color:#fca5a5; padding:1rem;">❌ 分析失敗: ${escapeHtml(ctx.error || '')}</div>`;
    return;
  }
  // result
  const a = ctx.analysis || {};
  const subjGapsHtml = (a.subject_gaps || []).map(s => {
    const pColor = { '高': '#fca5a5', '中': '#fbbf24', '低': '#86efac' }[s.priority] || '#a1a1aa';
    const gap = typeof s.gap === 'number' ? s.gap : (s.target - s.current);
    return `
      <div style="background:rgba(255,255,255,0.04); border-left:3px solid ${pColor}; border-radius:6px; padding:0.6rem 0.75rem; margin-bottom:0.4rem;">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.3rem;">
          <div>
            <span style="font-weight:700; color:#e4e4e7;">${escapeHtml(s.subject)}</span>
            <span style="background:rgba(255,255,255,0.1); color:${pColor}; padding:0.1rem 0.5rem; border-radius:4px; font-size:0.7rem; margin-left:0.4rem;">優先度${escapeHtml(s.priority)}</span>
          </div>
          <div style="font-size:0.85rem;">
            <span style="color:#a1a1aa;">現状 ${s.current}</span>
            <span style="color:#71717a;"> → 目標 </span>
            <span style="color:#86efac;">${s.target}</span>
            <span style="color:${gap > 0 ? '#fca5a5' : '#86efac'}; font-weight:700; margin-left:0.4rem;">(${gap > 0 ? '+' : ''}${gap})</span>
          </div>
        </div>
        ${s.trend_comment ? `<div style="font-size:0.78rem; color:#a1a1aa; margin-top:0.2rem;">📈 ${escapeHtml(s.trend_comment)}</div>` : ''}
      </div>`;
  }).join('');
  const adjustments = a.phase_adjustments || [];
  const adjHtml = adjustments.map((adj, i) => `
    <div style="background:rgba(167,139,250,0.06); border:1px solid rgba(167,139,250,0.3); border-radius:8px; padding:0.7rem; margin-bottom:0.4rem;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.3rem;">
        <div style="font-weight:700; color:#c4b5fd; font-size:0.88rem;">📝 ${escapeHtml(adj.phase_name || `フェーズ${(adj.phase_index||0)+1}`)}</div>
        <span style="background:rgba(167,139,250,0.2); color:#c4b5fd; padding:0.1rem 0.5rem; border-radius:4px; font-size:0.72rem; font-weight:700;">${escapeHtml(adj.action || '修正')}</span>
      </div>
      <div style="font-size:0.85rem; color:#e4e4e7; margin-bottom:0.3rem;">${escapeHtml(adj.detail || '')}</div>
      ${adj.new_materials && adj.new_materials.length ? `<div style="font-size:0.78rem; color:#a1a1aa;">📚 追加教材: ${adj.new_materials.map(m => `<span style="background:rgba(99,102,241,0.15); color:#c7d2fe; padding:0.1rem 0.4rem; border-radius:4px; margin-right:0.2rem; display:inline-block; margin-bottom:0.2rem;">${escapeHtml(m)}</span>`).join('')}</div>` : ''}
      ${adj.new_sapuri_lectures && adj.new_sapuri_lectures.length ? `<div style="font-size:0.78rem; color:#a1a1aa; margin-top:0.2rem;">📺 追加スタサプ: ${adj.new_sapuri_lectures.map(m => `<span style="background:rgba(251,113,133,0.15); color:#fda4af; padding:0.1rem 0.4rem; border-radius:4px; margin-right:0.2rem; display:inline-block; margin-bottom:0.2rem;">${escapeHtml(m)}</span>`).join('')}</div>` : ''}
    </div>
  `).join('');

  body.innerHTML = `
    <div style="background:rgba(0,0,0,0.3); border-radius:8px; padding:0.85rem; margin-bottom:0.8rem;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem; flex-wrap:wrap; gap:0.4rem;">
        <div style="font-weight:700; color:#fbbf24;">🎯 ${escapeHtml(ctx.curriculum.target_university)}${ctx.curriculum.target_faculty ? ` <span style="color:#a1a1aa; font-size:0.85rem;">${escapeHtml(ctx.curriculum.target_faculty)}</span>` : ''}</div>
        <div style="font-size:0.85rem; color:#a1a1aa;">入試まで ${ctx.remain_days} 日</div>
      </div>
      <div style="display:flex; gap:0.7rem; flex-wrap:wrap; font-size:0.85rem;">
        <div style="background:rgba(99,102,241,0.15); color:#c7d2fe; padding:0.3rem 0.7rem; border-radius:6px;">目標偏差値: <strong>${escapeHtml(String(a.target_deviation || '?'))}</strong></div>
        <div style="background:rgba(255,255,255,0.05); color:#e4e4e7; padding:0.3rem 0.7rem; border-radius:6px;">現状: <strong>${escapeHtml(String(a.current_average || '?'))}</strong></div>
      </div>
    </div>
    ${a.gap_summary ? `<div style="background:rgba(245,158,11,0.08); border-left:4px solid #f59e0b; padding:0.7rem; border-radius:6px; margin-bottom:0.8rem; font-size:0.88rem; color:#e4e4e7;">📊 <strong style="color:#fbbf24;">総合分析:</strong> ${escapeHtml(a.gap_summary)}</div>` : ''}
    <div style="font-weight:700; color:#c4b5fd; font-size:0.9rem; margin-bottom:0.4rem;">📐 科目別ギャップ</div>
    ${subjGapsHtml}
    ${adjustments.length ? `
      <div style="font-weight:700; color:#c4b5fd; font-size:0.9rem; margin:0.8rem 0 0.4rem;">✏️ カリキュラム修正提案</div>
      ${adjHtml}
    ` : '<div style="text-align:center; color:#71717a; padding:0.8rem;">大きな修正提案はありません (現行カリキュラムで順調)</div>'}
    ${a.overall_recommendation ? `<div style="background:rgba(16,185,129,0.08); border-left:4px solid #10b981; padding:0.7rem; border-radius:6px; margin-top:0.8rem; font-size:0.88rem; color:#e4e4e7;">💪 <strong style="color:#86efac;">戦略アドバイス:</strong> ${escapeHtml(a.overall_recommendation)}</div>` : ''}
    ${adjustments.length ? `
      <div style="display:flex; gap:0.5rem; margin-top:1rem;">
        <button id="gapApplyBtn" type="button" style="flex:1; padding:0.75rem; background:linear-gradient(135deg,#a78bfa,#ec4899); border:0; border-radius:8px; color:#fff; font-weight:800; cursor:pointer;">✨ AI 提案をカリキュラムに反映 (${adjustments.length} 件)</button>
        <button id="gapDismissBtn" type="button" style="padding:0.75rem 1.2rem; background:rgba(255,255,255,0.08); border:0; border-radius:8px; color:#a1a1aa; cursor:pointer;">後で考える</button>
      </div>
      <div id="gapApplyMsg" style="margin-top:0.5rem; font-size:0.78rem; min-height:1em;"></div>
    ` : `
      <div style="margin-top:1rem; text-align:center;">
        <button id="gapDismissBtn" type="button" style="padding:0.75rem 1.5rem; background:rgba(255,255,255,0.08); border:0; border-radius:8px; color:#c7d2fe; cursor:pointer;">確認した</button>
      </div>
    `}
    <div style="font-size:0.7rem; color:#71717a; margin-top:0.7rem; text-align:right;">model: ${escapeHtml(ctx.model || 'gemini-2.5-flash')} ・ AI による参考分析 (最終判断は塾長と相談)</div>`;

  const dismissBtn = body.querySelector('#gapDismissBtn');
  if (dismissBtn) dismissBtn.addEventListener('click', () => modal.style.display = 'none');
  const applyBtn = body.querySelector('#gapApplyBtn');
  if (applyBtn) applyBtn.addEventListener('click', async () => {
    if (!confirm(`カリキュラムに ${adjustments.length} 件の修正を反映しますか?`)) return;
    applyBtn.disabled = true; applyBtn.textContent = '反映中...';
    const m = body.querySelector('#gapApplyMsg');
    try {
      const res = await slApiFetch(`/api/curricula/${encodeURIComponent(ctx.curriculum.id)}/apply-gap-fix`, {
        method: 'POST',
        body: JSON.stringify({ phase_adjustments: adjustments }),
      });
      m.style.color = '#86efac'; m.textContent = `✅ ${res.applied} 件のフェーズに反映しました`;
      applyBtn.textContent = '✅ 反映完了';
      // カリキュラム一覧を更新
      if (typeof loadMyCurricula === 'function') await loadMyCurricula();
      setTimeout(() => { modal.style.display = 'none'; }, 1500);
    } catch (e) {
      m.style.color = '#fca5a5'; m.textContent = '❌ ' + (e.message || '反映失敗');
      applyBtn.disabled = false; applyBtn.textContent = `✨ AI 提案をカリキュラムに反映 (${adjustments.length} 件)`;
    }
  });
}

// ============================================================
// 📚 宿題セクション (Phase 5 - 国公立難関大学コース + 同等プラン限定)
// 塾長指示 2026-05-24: 国公立難関大学コースの子達に宿題タブを追加
// ============================================================
function _hwEscape(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c]));
}

function _hwDueDateBadge(dueDate, status) {
  if (!dueDate) return '';
  const today = new Date(); today.setHours(0,0,0,0);
  const due = new Date(dueDate + 'T00:00:00');
  const days = Math.floor((due - today) / 86400000);
  if (status === 'completed') {
    return `<span style="font-size:0.74rem; padding:2px 7px; background:rgba(52,211,153,0.18); color:#6ee7b7; border-radius:8px;">期限 ${_hwEscape(dueDate)}</span>`;
  }
  if (days < 0) {
    return `<span style="font-size:0.74rem; padding:2px 7px; background:rgba(239,68,68,0.18); color:#fca5a5; border-radius:8px; font-weight:bold;">⚠ 期限超過 (${_hwEscape(dueDate)})</span>`;
  }
  if (days === 0) {
    return `<span style="font-size:0.74rem; padding:2px 7px; background:rgba(251,191,36,0.22); color:#fde68a; border-radius:8px; font-weight:bold;">🔥 今日が期限</span>`;
  }
  if (days <= 3) {
    return `<span style="font-size:0.74rem; padding:2px 7px; background:rgba(251,191,36,0.16); color:#fde68a; border-radius:8px;">あと ${days} 日 (${_hwEscape(dueDate)})</span>`;
  }
  return `<span style="font-size:0.74rem; padding:2px 7px; background:rgba(255,255,255,0.06); color:#a1a1aa; border-radius:8px;">期限 ${_hwEscape(dueDate)}</span>`;
}

function _renderHomeworkItem(item) {
  const isOpen = item.status === 'open';
  const dueBadge = _hwDueDateBadge(item.due_date, item.status);
  const subjectBadge = item.subject
    ? `<span style="font-size:0.72rem; padding:2px 7px; background:rgba(99,102,241,0.2); color:#a5b4fc; border-radius:8px; margin-right:6px;">${_hwEscape(item.subject)}</span>`
    : '';
  const desc = item.description
    ? `<div style="color:#cbd5e1; font-size:0.86rem; line-height:1.6; margin-top:6px; white-space:pre-wrap;">${_hwEscape(item.description)}</div>`
    : '';
  const completedBlock = (!isOpen && item.completed_at)
    ? `<div style="margin-top:8px; padding:8px 11px; background:rgba(52,211,153,0.08); border-left:3px solid #34d399; border-radius:6px; font-size:0.78rem; color:#6ee7b7;">
         ✅ 完了 (${_hwEscape(String(item.completed_at).slice(0,16).replace('T',' '))})
         ${item.student_note ? `<div style="color:#cbd5e1; margin-top:4px; white-space:pre-wrap;">${_hwEscape(item.student_note)}</div>` : ''}
       </div>`
    : '';
  // 📄 添付プリント (配布プリント) があれば「PDFを開く」ボタン
  const printBtn = (item.attachment_print && item.attachment_print.id)
    ? `<button type="button" data-hw-print="${_hwEscape(item.attachment_print.id)}" style="margin-top:10px; margin-right:8px; padding:8px 14px; background:rgba(59,130,246,0.18); color:#93c5fd; border:1px solid rgba(59,130,246,0.4); border-radius:8px; font-weight:bold; font-size:0.84rem; cursor:pointer;">📄 PDFを開く${item.attachment_print.title ? '（' + _hwEscape(item.attachment_print.title) + '）' : ''}</button>`
    : '';
  const completeBtn = isOpen
    ? `<button type="button" data-hw-complete="${_hwEscape(item.id)}" style="margin-top:10px; padding:8px 16px; background:linear-gradient(135deg,#34d399,#10b981); color:#fff; border:0; border-radius:8px; font-weight:bold; font-size:0.86rem; cursor:pointer;">✅ 完了する</button>`
    : '';
  return `<div class="hw-item" data-hw-id="${_hwEscape(item.id)}" style="padding:14px 16px; background:${isOpen ? 'rgba(0,0,0,0.25)' : 'rgba(255,255,255,0.02)'}; border:1px solid ${isOpen ? 'rgba(99,102,241,0.3)' : 'rgba(255,255,255,0.06)'}; border-radius:10px; margin-bottom:10px;">
    <div style="display:flex; align-items:center; flex-wrap:wrap; gap:8px;">
      ${subjectBadge}${dueBadge}
    </div>
    <div style="margin-top:8px; color:${isOpen ? '#fff' : '#a1a1aa'}; font-weight:bold; font-size:0.96rem; ${isOpen ? '' : 'text-decoration:line-through;'}">${_hwEscape(item.title)}</div>
    ${desc}
    ${completedBlock}
    <div>${printBtn}${completeBtn}</div>
  </div>`;
}

// 📝 英文法ドリルを「宿題カード」として描画 (2026-06-16 塾長指示「ドリルも宿題に入れる」)。
// クリック → window._gdOpenDrill(drill_id) が解答エリア(#grammarDrillSection)に問題を展開する。
function _renderDrillAsHwItem(item) {
  const isOpen = item.status !== 'completed';
  const typeBadge = `<span style="font-size:0.72rem; padding:2px 7px; background:rgba(20,184,166,0.22); color:#5eead4; border-radius:8px; font-weight:bold;">📝 英文法ドリル</span>`;
  const unitBadge = item.unit
    ? `<span style="font-size:0.72rem; padding:2px 7px; background:rgba(99,102,241,0.2); color:#a5b4fc; border-radius:8px;">${_hwEscape(item.unit)}</span>`
    : '';
  const levelBadge = item.level
    ? `<span style="font-size:0.72rem; padding:2px 7px; background:rgba(255,255,255,0.06); color:#a1a1aa; border-radius:8px;">${_hwEscape(item.level)}</span>`
    : '';
  const scoreBlock = (!isOpen && item.score_total != null)
    ? `<div style="margin-top:8px; padding:8px 11px; background:rgba(52,211,153,0.08); border-left:3px solid #34d399; border-radius:6px; font-size:0.78rem; color:#6ee7b7;">✅ 完了 スコア ${_hwEscape(String(item.score_correct == null ? '?' : item.score_correct))}/${_hwEscape(String(item.score_total))}</div>`
    : '';
  const cta = isOpen ? '▶ 解いて提出する' : '結果・解説を見る ▶';
  const btnStyle = isOpen
    ? 'background:linear-gradient(135deg,#14b8a6,#10b981); color:#fff; border:0;'
    : 'background:rgba(255,255,255,0.05); color:#a1a1aa; border:1px solid rgba(255,255,255,0.12);';
  const btn = `<button type="button" data-hw-drill-open="${_hwEscape(item.drill_id)}" style="margin-top:10px; padding:8px 16px; ${btnStyle} border-radius:8px; font-weight:bold; font-size:0.86rem; cursor:pointer;">${cta}</button>`;
  return `<div class="hw-item hw-drill-item" style="padding:14px 16px; background:${isOpen ? 'rgba(0,0,0,0.25)' : 'rgba(255,255,255,0.02)'}; border:1px solid ${isOpen ? 'rgba(20,184,166,0.3)' : 'rgba(255,255,255,0.06)'}; border-radius:10px; margin-bottom:10px;">
    <div style="display:flex; align-items:center; flex-wrap:wrap; gap:8px;">${typeBadge}${unitBadge}${levelBadge}</div>
    <div style="margin-top:8px; color:${isOpen ? '#fff' : '#a1a1aa'}; font-weight:bold; font-size:0.96rem;">${_gdRich(item.title)}</div>
    ${scoreBlock}
    <div>${btn}</div>
  </div>`;
}

async function initHomeworkSection() {
  const section = document.querySelector('.homework-section');
  if (!section) return;
  const student = getCurrentStudent();
  // 宿題 (homework_assignments) は対象コース/プラン限定。英文法ドリルは全生徒に配信されうるため、
  // 「ドリルがある非対象生徒」にも宿題セクションを出してドリルを宿題として見せる (塾長指示 2026-06-16)。
  const premium = _canUseStudyMgmt(student);

  const list = section.querySelector('#homeworkList');
  const badge = section.querySelector('#homeworkBadge');
  const toggleWrap = section.querySelector('#homeworkCompletedToggle');
  const toggleBtn = section.querySelector('#homeworkShowCompleted');
  if (!list) return;

  // 非premium (宿題=homework 対象外) は「英文法ドリル」専用見出しに切替 (宿題は出ないため misleading 回避)
  const titleEl = section.querySelector('#homeworkTitleText');
  const introEl = section.querySelector('#homeworkIntro');
  if (!premium) {
    if (titleEl) titleEl.textContent = '📝 英文法ドリル';
    if (introEl) introEl.textContent = '英文法ドリルです。「▶ 解いて提出する」を押して取り組みましょう。';
  }

  let openHw = [], doneHw = [], overdueN = 0;
  let openDrills = [], doneDrills = [];
  let showCompleted = false;
  let previewMode = false;   // preview(?preview_mode=) no-op 検出 → section 非表示 (旧 teal 挙動を踏襲)
  let drillsFailed = false;  // ドリル取得の「真の失敗」検出 → 空と区別しエラー表示 (非表示にしない)

  // 宿題 (premium のみ・403/失敗時はドリルだけで続行)
  async function loadHomework() {
    openHw = []; doneHw = []; overdueN = 0;
    if (!premium) return;
    try {
      const data = await slApiFetch('/api/student/homework?limit=100');
      const items = (data && data.items) || [];
      openHw = items.filter(it => it.status === 'open');
      doneHw = items.filter(it => it.status === 'completed');
      overdueN = (data.summary && data.summary.overdue) || 0;
    } catch (e) {
      if (e && e.preview) { previewMode = true; return; }
      console.warn('[hw] homework load failed (ドリルのみ表示):', e && (e.message || e));
    }
  }

  // 英文法ドリル (全生徒・配信されていれば宿題として表示)
  async function loadDrills() {
    openDrills = []; doneDrills = []; drillsFailed = false;
    try {
      const data = await slApiFetch('/api/student/grammar-drills');
      const items = (data && data.items) || [];
      openDrills = items.filter(it => it.status !== 'completed');
      doneDrills = items.filter(it => it.status === 'completed');
    } catch (e) {
      // preview(no-op) は section 非表示。真の失敗 (500/network) は「ドリル有無不明」なので
      // 空と区別して section は出しエラー表示する (旧 teal loadList の安全網を踏襲)。
      if (e && e.preview) { previewMode = true; }
      else { drillsFailed = true; console.warn('[hw] grammar-drills load failed:', e && (e.message || e)); }
    }
  }

  async function refresh() {
    previewMode = false;
    await Promise.all([loadHomework(), loadDrills()]);
    // preview(?preview_mode=) は no-op → section 非表示 (旧 teal セクションの e.preview 挙動を踏襲)。
    if (previewMode) { section.style.display = 'none'; return; }
    // それ以外は常時表示 (2026-06-09 塾長指示「宿題欄を常時表示に改修」: 配信0件でも空状態で発見性を担保。
    //   非premium でドリル0件でも「📝 英文法ドリル」の空状態を出す=ドリルがどこに来るか常に分かる)。
    section.style.display = 'block';
    // badge: 未完了(宿題 + ドリル)
    const openTotal = openHw.length + openDrills.length;
    if (openTotal > 0) {
      badge.style.display = 'inline-block';
      if (overdueN > 0) {
        badge.textContent = `⚠ 期限超過 ${overdueN} / 未完了 ${openTotal}`;
        badge.style.background = '#ef4444';
      } else {
        badge.textContent = `未完了 ${openTotal}`;
        badge.style.background = '#6366f1';
      }
    } else {
      badge.style.display = 'none';
    }
    render();
  }

  function render() {
    // ドリル取得が真に失敗した時はエラーを明示 (空と誤認させない・旧 teal の安全網を踏襲)
    const errBanner = drillsFailed
      ? `<div style="color:#fca5a5; padding:12px; background:rgba(239,68,68,0.08); border-radius:8px; font-size:0.85rem; margin-bottom:10px;">⚠ ドリルの取得に失敗しました。ページを再読み込み（更新）してみてください。</div>`
      : '';
    const emptyMsg = premium ? '📭 いま出ている宿題・ドリルはありません。' : '📭 いま出ている英文法ドリルはありません。';
    const totalAll = openHw.length + doneHw.length + openDrills.length + doneDrills.length;
    if (totalAll === 0) {
      list.innerHTML = errBanner + `<div style="color:#71717a; text-align:center; padding:1.5rem 0; font-size:0.88rem;">${emptyMsg}<br><span style="font-size:0.74rem;">塾長が出すと、ここに表示されます。最近やったのに無い時は、ページを再読み込みしてみてください。</span></div>`;
      toggleWrap.style.display = 'none';
      return;
    }
    let html = errBanner;
    // 未完了: 英文法ドリルを先頭に (やってもらいたい) → 宿題
    const openCards = openDrills.map(_renderDrillAsHwItem).concat(openHw.map(_renderHomeworkItem));
    if (openCards.length > 0) {
      html += openCards.join('');
    } else {
      html += `<div style="color:#86efac; text-align:center; padding:1rem 0; font-size:0.9rem;">🎉 未完了の宿題・ドリルはありません。素晴らしい!</div>`;
    }
    const doneCount = doneHw.length + doneDrills.length;
    if (showCompleted && doneCount > 0) {
      html += `<div style="margin-top:1.5rem; padding-top:1rem; border-top:1px dashed rgba(255,255,255,0.08);">
        <div style="color:#a1a1aa; font-size:0.78rem; margin-bottom:8px;">✅ 過去の完了 (直近 ${doneCount} 件・タップで復習)</div>
        ${doneDrills.map(_renderDrillAsHwItem).join('')}${doneHw.map(_renderHomeworkItem).join('')}
      </div>`;
    }
    list.innerHTML = html;
    // toggle 表示制御
    if (doneCount > 0) {
      toggleWrap.style.display = 'block';
      toggleBtn.textContent = showCompleted
        ? `過去の完了を隠す ▴`
        : `過去の完了を表示 (${doneCount}) ▾`;
    } else {
      toggleWrap.style.display = 'none';
    }
  }

  // 🔁 ドリル解答エリアの「← 一覧に戻る」/ 提出後 から宿題リストを再読込するためのフック
  window._hwRefreshDrills = refresh;

  // 📄 添付プリント「PDFを開く」(event delegation)。download endpoint で file_path を取得 → 検証 → 新タブ表示。
  list.addEventListener('click', async (e) => {
    const pbtn = e.target.closest && e.target.closest('[data-hw-print]');
    if (!pbtn) return;
    const pid = pbtn.getAttribute('data-hw-print');
    if (!pid) return;
    pbtn.disabled = true; const _orig = pbtn.textContent; pbtn.textContent = '⏳ 準備中…';
    try {
      // slApiFetch は成功時に parse 済み JSON を返す (Response ではない)
      const data = await slApiFetch(`/api/student/lesson-prints/${encodeURIComponent(pid)}/download`, { method: 'POST', body: JSON.stringify({}) });
      let fpath = String((data && data.file_path) || '').replace(/\+/g, '-');
      // 既存プリントビューアと同じ path 検証 (lesson-prints 配下の .pdf のみ・.. 不可)
      if (!/^\/lesson-prints\/[^?#\s]+\.pdf$/i.test(fpath) || fpath.includes('..')) {
        alert('⚠️ PDFの取得に失敗しました'); return;
      }
      window.open(fpath, '_blank', 'noopener,noreferrer');
    } catch (e3) {
      alert('❌ PDFを開けませんでした: ' + (e3.message || e3));
    } finally {
      setTimeout(() => { pbtn.textContent = _orig; pbtn.disabled = false; }, 800);
    }
  });

  // 完了ボタン (event delegation)
  list.addEventListener('click', async (e) => {
    const btn = e.target.closest && e.target.closest('[data-hw-complete]');
    if (!btn) return;
    const hwId = btn.getAttribute('data-hw-complete');
    if (!hwId) return;
    if (!confirm('この宿題を完了にしますか?')) return;
    btn.disabled = true; btn.textContent = '⏳ 送信中...';
    try {
      await slApiFetch(`/api/student/homework/${encodeURIComponent(hwId)}/complete`, {
        method: 'POST',
        body: JSON.stringify({}),
      });
      // 軽い祝福 toast
      try {
        const toast = document.createElement('div');
        toast.textContent = '🎉 お疲れさま! 完了しました';
        toast.style.cssText = 'position:fixed; top:80px; left:50%; transform:translateX(-50%); padding:12px 24px; background:linear-gradient(135deg,#34d399,#10b981); color:#fff; border-radius:10px; font-weight:bold; box-shadow:0 8px 24px rgba(0,0,0,0.3); z-index:10000;';
        document.body.appendChild(toast);
        setTimeout(() => { toast.style.transition = 'opacity 0.4s'; toast.style.opacity = '0'; }, 2200);
        setTimeout(() => toast.remove(), 2700);
      } catch {}
      await refresh();
    } catch (e2) {
      alert('❌ 完了処理に失敗しました: ' + (e2.message || e2));
      btn.disabled = false; btn.textContent = '✅ 完了する';
    }
  });

  // 📝 ドリルを開く (event delegation) — 解答エリア(#grammarDrillSection)に展開
  list.addEventListener('click', (e) => {
    const dbtn = e.target.closest && e.target.closest('[data-hw-drill-open]');
    if (!dbtn) return;
    const did = dbtn.getAttribute('data-hw-drill-open');
    if (!did) return;
    if (typeof window._gdOpenDrill === 'function') {
      window._gdOpenDrill(did);
    } else {
      alert('ドリルを開けませんでした。ページを再読み込みしてください。');
    }
  });

  // toggle 完了履歴
  toggleBtn.addEventListener('click', () => {
    showCompleted = !showCompleted;
    render();
  });

  await refresh();
}

// ==========================================================================
// 📝 単元別ドリル (英文法 4 択ドリル・2026-06-05)
//   - 2026-06-16 役割変更: ドリル一覧は initHomeworkSection (📚 宿題) に統合済み。
//     この section (#grammarDrillSection) は「解答エリア」専用で、宿題カードの「▶ 解いて提出する」
//     から openDrill() が表示する。一覧の常時表示・空状態・発見性 (2026-06-09 塾長指示) は
//     initHomeworkSection 側で担保 (premium 不問・配信0件でも空状態・preview のみ非表示)。
//   - 配信されていれば誰でも解ける (course ゲート無し)。認証は slApiFetch() 経由。
//   - stem/explanation/choices/title は全て _gdEscape (= escapeHtml ベース) でエスケープ後に表示。
//     さらに stem/explanation は <u>...</u> を復活 (下線対応・既存 3 ファイル whitelist 方式に準拠) し、
//     $$/\[/\( の数式を KaTeX で組版 (learning-brain.js の _lbApplyKatex と同方式・CDN defer retry 付き)。
// ==========================================================================

// XSS エスケープ (homework の _hwEscape と同様・グローバル escapeHtml に委譲)
function _gdEscape(s) {
  return escapeHtml(s);
}

// 下線対応: エスケープ済み文字列の中の &lt;u&gt;...&lt;/u&gt; だけを <u>...</u> に復活。
// (english-exam.js / learning-brain.js / mock-exam.js の whitelist 復活方式に準拠。属性は付けない)
function _gdRestoreUnderline(escaped) {
  return String(escaped == null ? '' : escaped)
    .replace(/&lt;u&gt;/g, '<u>')
    .replace(/&lt;\/u&gt;/g, '</u>');
}

// stem/explanation 用: エスケープ → <u> 復活 (数式 delimiters はそのまま残し KaTeX に渡す)
function _gdRich(s) {
  return _gdRestoreUnderline(_gdEscape(s));
}

// 🧮 KaTeX 自動組版 (CDN defer load 対応で未ロード時はリトライ・learning-brain.js _lbApplyKatex と同方式)。
//   delimiters は $$ / \[ / \( + 単一 $ (英文法ドリルは通貨 $ を含まない前提・stem の $...$ 数式を拾うため)。
function _gdApplyKatex(rootEl) {
  if (!rootEl) return;
  const run = () => {
    if (typeof window.renderMathInElement !== 'function') return false;
    try {
      window.renderMathInElement(rootEl, {
        delimiters: [
          { left: '$$', right: '$$', display: true },
          { left: '\\[', right: '\\]', display: true },
          { left: '\\(', right: '\\)', display: false },
          { left: '$', right: '$', display: false },
        ],
        throwOnError: false,
        errorColor: '#f87171',
        strict: 'ignore',
      });
    } catch (e) { console.warn('[GD katex] render failed', e); }
    return true;
  };
  if (run()) return;
  let tries = 0;
  const id = setInterval(() => { tries++; if (run() || tries > 20) clearInterval(id); }, 200);
}

// (2026-06-16) ドリル一覧の行/バッジ描画はここから削除: 一覧は 📚 宿題セクション
//   (_renderDrillAsHwItem) に統合し、この section は解答エリア専用になったため。
//   完了バッジ等の表示は _renderDrillAsHwItem 側で宿題カードとして描画する。

// 1 問の選択肢ラジオ群を描画 (表示は ①②③④ = index+1、value は 0 始まり index)
function _gdRenderChoices(drillId, q) {
  const marks = ['①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧'];
  const choices = Array.isArray(q.choices) ? q.choices : [];
  const name = `gd_${_gdEscape(String(drillId))}_q_${_gdEscape(String(q.question_id))}`;
  return choices.map((c, i) => {
    const mark = marks[i] || `(${i + 1})`;
    return `<label class="gd-choice" style="display:flex; align-items:flex-start; gap:8px; padding:9px 11px; background:rgba(0,0,0,0.25); border:1px solid rgba(255,255,255,0.1); border-radius:8px; margin-bottom:7px; cursor:pointer;">
      <input type="radio" name="${name}" value="${i}" data-gd-qid="${_gdEscape(String(q.question_id))}" style="margin-top:3px; flex:0 0 auto;">
      <span style="color:#e2e8f0; font-size:0.9rem; line-height:1.5;"><span style="color:#5eead4; font-weight:bold; margin-right:4px;">${mark}</span>${_gdRich(c)}</span>
    </label>`;
  }).join('');
}

// 解答前 / 復習表示の 1 問ブロック
function _gdRenderQuestionBlock(drillId, q, opts) {
  opts = opts || {};
  const review = !!opts.review; // 完了済みドリルの復習表示か
  const marks = ['①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧'];
  let body;
  if (review) {
    // 完了済み: your_answer / answer(正解 index) / explanation を表示。間違えた問だけ explanation を展開。
    const yourIdx = (q.your_answer == null) ? null : Number(q.your_answer);
    const correctIdx = (q.answer == null) ? null : Number(q.answer);
    const isCorrect = (yourIdx != null && correctIdx != null && yourIdx === correctIdx);
    const choices = Array.isArray(q.choices) ? q.choices : [];
    const choiceLines = choices.map((c, i) => {
      const mark = marks[i] || `(${i + 1})`;
      const isYour = (yourIdx === i);
      const isCorr = (correctIdx === i);
      let bg = 'rgba(0,0,0,0.2)', border = 'rgba(255,255,255,0.08)', tag = '';
      if (isCorr) { bg = 'rgba(52,211,153,0.12)'; border = 'rgba(52,211,153,0.45)'; tag = ' <span style="color:#6ee7b7; font-weight:bold;">✓ 正解</span>'; }
      if (isYour && !isCorr) { bg = 'rgba(239,68,68,0.12)'; border = 'rgba(239,68,68,0.45)'; tag = ' <span style="color:#fca5a5; font-weight:bold;">✗ あなたの解答</span>'; }
      else if (isYour && isCorr) { tag = ' <span style="color:#6ee7b7; font-weight:bold;">← あなたの解答 ✓</span>'; }
      return `<div style="padding:8px 11px; background:${bg}; border:1px solid ${border}; border-radius:8px; margin-bottom:6px; font-size:0.9rem; color:#e2e8f0; line-height:1.5;"><span style="color:#5eead4; font-weight:bold; margin-right:4px;">${mark}</span>${_gdRich(c)}${tag}</div>`;
    }).join('');
    body = choiceLines + _gdExplanationBlock(q, isCorrect);
  } else {
    body = _gdRenderChoices(drillId, q);
  }
  const statusMark = review
    ? ((q.your_answer != null && q.answer != null && Number(q.your_answer) === Number(q.answer))
        ? '<span style="color:#6ee7b7;">✓</span>' : '<span style="color:#fca5a5;">✗</span>')
    : '';
  return `<div class="gd-q" data-gd-q-block="${_gdEscape(String(q.question_id))}" style="padding:14px 15px; background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.08); border-radius:10px; margin-bottom:12px;">
    <div style="font-weight:bold; color:#fff; font-size:0.95rem; margin-bottom:10px; line-height:1.6;"><span style="color:#5eead4; margin-right:6px;">Q${_gdEscape(String(q.no))}.</span> ${statusMark} ${_gdRich(q.stem)}</div>
    ${body}
  </div>`;
}

// 解説ブロック: 間違えた問題だけ explanation を展開表示 (正解時は折りたたみ表示)
function _gdExplanationBlock(q, isCorrect) {
  const expl = q.explanation;
  if (!expl) return '';
  if (isCorrect) {
    // 正解は控えめに (details で任意展開)
    return `<details style="margin-top:8px;"><summary style="cursor:pointer; color:#6ee7b7; font-size:0.8rem;">📖 解説を見る</summary><div style="margin-top:6px; padding:9px 12px; background:rgba(52,211,153,0.06); border-left:3px solid #34d399; border-radius:6px; font-size:0.85rem; color:#cbd5e1; line-height:1.65; white-space:pre-wrap;">${_gdRich(expl)}</div></details>`;
  }
  // 誤答は常に展開
  return `<div style="margin-top:8px; padding:9px 12px; background:rgba(239,68,68,0.07); border-left:3px solid #ef4444; border-radius:6px; font-size:0.85rem; color:#fde68a; line-height:1.65;"><span style="color:#fca5a5; font-weight:bold;">📖 解説</span><div style="color:#cbd5e1; margin-top:4px; white-space:pre-wrap;">${_gdRich(expl)}</div></div>`;
}

// 採点結果 (submit レスポンス results[]) の 1 問
function _gdRenderResultItem(r) {
  const marks = ['①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧'];
  const choices = Array.isArray(r.choices) ? r.choices : [];
  const yourIdx = (r.your_answer == null) ? null : Number(r.your_answer);
  const correctIdx = (r.correct_answer == null) ? null : Number(r.correct_answer);
  const isCorrect = !!r.is_correct;
  const choiceLines = choices.map((c, i) => {
    const mark = marks[i] || `(${i + 1})`;
    const isYour = (yourIdx === i);
    const isCorr = (correctIdx === i);
    let bg = 'rgba(0,0,0,0.2)', border = 'rgba(255,255,255,0.08)', tag = '';
    if (isCorr) { bg = 'rgba(52,211,153,0.12)'; border = 'rgba(52,211,153,0.45)'; tag = ' <span style="color:#6ee7b7; font-weight:bold;">✓ 正解</span>'; }
    if (isYour && !isCorr) { bg = 'rgba(239,68,68,0.12)'; border = 'rgba(239,68,68,0.45)'; tag = ' <span style="color:#fca5a5; font-weight:bold;">✗ あなたの解答</span>'; }
    else if (isYour && isCorr) { tag = ' <span style="color:#6ee7b7; font-weight:bold;">← あなたの解答 ✓</span>'; }
    return `<div style="padding:8px 11px; background:${bg}; border:1px solid ${border}; border-radius:8px; margin-bottom:6px; font-size:0.9rem; color:#e2e8f0; line-height:1.5;"><span style="color:#5eead4; font-weight:bold; margin-right:4px;">${mark}</span>${_gdRich(c)}${tag}</div>`;
  }).join('');
  const head = isCorrect
    ? '<span style="color:#6ee7b7; font-weight:bold;">✓ 正解</span>'
    : '<span style="color:#fca5a5; font-weight:bold;">✗ 不正解</span>';
  // 間違えた問題だけ explanation を展開 (正解は details で任意展開)
  const explBlock = _gdExplanationBlock({ explanation: r.explanation }, isCorrect);
  return `<div style="padding:14px 15px; background:rgba(255,255,255,0.02); border:1px solid ${isCorrect ? 'rgba(52,211,153,0.25)' : 'rgba(239,68,68,0.3)'}; border-radius:10px; margin-bottom:12px;">
    <div style="font-weight:bold; color:#fff; font-size:0.95rem; margin-bottom:10px; line-height:1.6;"><span style="color:#5eead4; margin-right:6px;">Q${_gdEscape(String(r.no))}.</span> ${head} <span style="margin-left:4px;">${_gdRich(r.stem)}</span></div>
    ${choiceLines}
    ${explBlock}
  </div>`;
}

// 📊 みんなの中での自分 (匿名・集団比較・2026-06-05)
// /api/student/comparison/overview は集計値のみ返す (他者の個人データなし)。
// 全項目データ不足/未受験なら section ごと非表示。
async function initComparisonSection() {
  const section = document.getElementById('comparisonSection');
  if (!section) return;
  const body = section.querySelector('#comparisonBody');
  const refreshBtn = section.querySelector('#comparisonRefresh');
  if (!body) return;

  function _cmpCard(title, badges, sub) {
    return `<div style="background:rgba(0,0,0,0.22);border-radius:10px;padding:0.7rem 0.85rem;">
      <div style="font-size:0.85rem;font-weight:700;color:#e5e7eb;margin-bottom:0.35rem;">${escapeHtml(title)}</div>
      <div style="display:flex;flex-wrap:wrap;gap:0.5rem 0.9rem;font-size:0.9rem;color:#cbd5e1;">${badges.filter(Boolean).join('<span style="color:#52525b;">・</span>')}</div>
      ${sub ? `<div style="font-size:0.75rem;color:#94a3b8;margin-top:0.35rem;">${escapeHtml(sub)}</div>` : ''}
    </div>`;
  }
  function _cmpMuted(title, msg) {
    return `<div style="background:rgba(0,0,0,0.13);border-radius:10px;padding:0.6rem 0.85rem;opacity:0.75;">
      <div style="font-size:0.85rem;font-weight:700;color:#a1a1aa;">${escapeHtml(title)}</div>
      <div style="font-size:0.76rem;color:#71717a;margin-top:0.2rem;">${escapeHtml(msg)}</div>
    </div>`;
  }
  // 未記録の子に「あなた0時間・最下位・みんなの平均」を赤系で見せて記録を促す(危機感カード)
  function _cmpWarn(title, badges, sub) {
    return `<div style="background:rgba(239,68,68,0.10);border:1px solid rgba(248,113,113,0.45);border-radius:10px;padding:0.7rem 0.85rem;">
      <div style="font-size:0.85rem;font-weight:700;color:#fca5a5;margin-bottom:0.35rem;">${escapeHtml(title)} <span style="font-size:0.9em;">⚠️</span></div>
      <div style="display:flex;flex-wrap:wrap;gap:0.5rem 0.9rem;font-size:0.9rem;color:#e5e7eb;">${badges.filter(Boolean).join('<span style="color:#52525b;">・</span>')}</div>
      ${sub ? `<div style="font-size:0.78rem;color:#fca5a5;margin-top:0.4rem;font-weight:600;">${escapeHtml(sub)}</div>` : ''}
    </div>`;
  }
  // 数値は Number 化してから埋め込む (サーバ由来でも念のため型を固定)
  const N = (v) => (v == null || isNaN(Number(v))) ? null : Number(v);

  async function load() {
    body.innerHTML = `<div style="color:#71717a;text-align:center;padding:1.2rem 0;font-size:0.85rem;">⏳ 読み込み中...</div>`;
    let data;
    try {
      data = await slApiFetch('/api/student/comparison/overview');
    } catch (e) {
      if (e && e.preview) { section.style.display = 'none'; return; }
      section.style.display = 'block';
      body.innerHTML = `<div style="color:#fca5a5;padding:12px;background:rgba(239,68,68,0.08);border-radius:8px;font-size:0.85rem;">⚠ 取得に失敗しました (${escapeHtml(String((e && (e.message || e)) || ''))})</div>`;
      return;
    }
    const cards = [];
    // ① 模試 (exam_type 別・集団内偏差値)。available が無ければ「準備中」案内を出す(常時表示)。
    const mockCards = [];
    ((data && data.mock_exams) || []).forEach(m => {
      if (!m || !m.available) return;
      const dev = N(m.deviation), rank = N(m.rank), pop = N(m.population), top = N(m.top_percent), my = N(m.my_value), avg = N(m.average);
      const badges = [
        (rank != null && pop != null) ? `${pop}人中 <b style="color:#fcd34d;font-size:1.15em;">${rank}位</b>` : null,
        (top != null && top <= 50) ? `上位 <b>${top}%</b>` : null,
        dev != null ? `偏差値 ${dev}` : null,
      ];
      const sub = (my != null && avg != null) ? `あなた ${my}% / みんなの平均 ${avg}%` : '';
      mockCards.push(_cmpCard('📝 模試: ' + String(m.exam_label || m.exam_type || ''), badges, sub));
    });
    if (mockCards.length) cards.push(...mockCards);
    else cards.push(_cmpMuted('📝 模試', 'アプリ内の模試を受けると、同じ模試を解いた人の中での偏差値・順位が出ます'));
    // ② 学習時間 (直近7日)
    const stt = data && data.study_time;
    if (stt && stt.available && stt.not_recorded && _isFreshStudent()) {
      // 🔰 2026-06-11 (低学力層オンボーディング): 初週の新規生徒に「あなた 0時間・最下位」の
      // 赤カードを初日から見せると自己効力感を折って離脱を招くため、初回訪問から 7 日間は
      // 中立の案内に置き換える。8 日目以降の未記録者には従来どおり危機感カードで記録を促す。
      cards.push(_cmpMuted('⏱ 学習時間 (直近7日)', '学習記録をつけはじめると、みんなとの比較がここに表示されます。まずは上の「コーチの今日の一手」から始めよう'));
    } else if (stt && stt.available && stt.not_recorded && N(stt.population) != null && N(stt.rank) != null) {
      // 未記録 → 危機感(赤系): あなた0時間・みんなの平均。促すのは「学習量」でなく「記録」(中学生配慮)。
      // 「未記録」「がんばっています」等の人格・努力断定は避け、記録行動への前向きな促しに留める。
      const avgH0 = (N(stt.average) / 60).toFixed(1);
      cards.push(_cmpWarn('⏱ 学習時間 (直近7日)',
        [`あなたの記録 <b style="color:#f87171;font-size:1.1em;">0時間</b>`, `${N(stt.population)}人中 <b style="color:#f87171;">${N(stt.rank)}位</b>`],
        `みんなは今週 平均 ${avgH0}時間 を記録しているよ。あなたも今日の分から学習記録をつけて、追いついていこう！`));
    } else if (stt && stt.available) {
      const myH = (N(stt.my_value) / 60).toFixed(1), avgH = (N(stt.average) / 60).toFixed(1);
      const diffH = (N(stt.diff_from_avg) / 60).toFixed(1);
      const sttTop = N(stt.top_percent);
      cards.push(_cmpCard('⏱ 学習時間 (直近7日)',
        [`<b style="color:#fcd34d;font-size:1.1em;">${myH}時間</b>`, `${N(stt.population)}人中 <b>${N(stt.rank)}位</b>`, (sttTop != null && sttTop <= 50) ? `上位 <b>${sttTop}%</b>` : null],
        `みんなの平均 ${avgH}時間 (あなた ${N(stt.diff_from_avg) >= 0 ? '+' : ''}${diffH}時間)`));
    } else if (stt && stt.reason === 'insufficient_population') {
      cards.push(_cmpMuted('⏱ 学習時間 (直近7日)', `あと${N(stt.need) - N(stt.population)}人ぶんの学習記録が集まれば表示されます`));
    } else {
      cards.push(_cmpMuted('⏱ 学習時間 (直近7日)', '学習時間を記録すると、みんなの中での順位が出ます'));
    }
    // ③ 問題の正解率 (直近30日)
    const acc = data && data.accuracy;
    if (acc && acc.available) {
      const accTop = N(acc.top_percent);
      cards.push(_cmpCard('🎯 問題の正解率 (直近30日)',
        [`あなた <b style="color:#fcd34d;font-size:1.1em;">${N(acc.my_value)}%</b>`, `${N(acc.population)}人中 <b>${N(acc.rank)}位</b>`, (accTop != null && accTop <= 50) ? `上位 <b>${accTop}%</b>` : null],
        `みんなの平均 ${N(acc.average)}% (あなた ${N(acc.diff_from_avg) >= 0 ? '+' : ''}${N(acc.diff_from_avg)}%)`));
    } else if (acc && acc.reason === 'insufficient_population') {
      cards.push(_cmpMuted('🎯 問題の正解率 (直近30日)', `あと${N(acc.need) - N(acc.population)}人ぶんのデータが集まれば表示されます`));
    } else {
      cards.push(_cmpMuted('🎯 問題の正解率 (直近30日)', 'ドリルや問題を解くと、みんなの中での正解率の位置が出ます'));
    }

    // 常に表示 (各項目: データありは中身 / 無しは「○○すると表示」案内)。preview時は上の catch で非表示維持。
    section.style.display = 'block';
    body.innerHTML = cards.join('');
  }

  if (refreshBtn) refreshBtn.addEventListener('click', () => { load(); });
  await load();
}

async function initGrammarDrillSection() {
  const section = document.getElementById('grammarDrillSection');
  if (!section) return;
  const list = section.querySelector('#grammarDrillList');
  const badge = section.querySelector('#grammarDrillBadge');
  if (!list) return;

  // 「← 一覧に戻る」= 解答エリアを閉じて宿題リストへ戻る (2026-06-16 ドリルは宿題セクションに統合済み)。
  // 解答/採点後にここを通り、宿題リストを再読込 (完了が反映される) して宿題セクションへスクロール。
  async function loadList() {
    section.style.display = 'none';
    list.innerHTML = '';
    if (typeof window._hwRefreshDrills === 'function') {
      try { await window._hwRefreshDrills(); } catch (_) { /* noop */ }
    }
    const hw = document.getElementById('homeworkSection');
    if (hw && hw.style.display !== 'none') {
      try { hw.scrollIntoView({ behavior: 'smooth', block: 'start' }); } catch (_) { /* noop */ }
    }
  }

  // ドリルを開く (GET /api/student/grammar-drill/{id}) — 宿題リストの「▶ 解いて提出する」から呼ばれる。
  async function openDrill(drillId) {
    section.style.display = 'block';  // 解答エリアを表示 (通常は非表示)
    try { section.scrollIntoView({ behavior: 'smooth', block: 'start' }); } catch (_) { /* noop */ }
    list.innerHTML = `<div style="color:#71717a; text-align:center; padding:1.2rem 0; font-size:0.85rem;">⏳ 読み込み中...</div>`;
    let data;
    try {
      data = await slApiFetch(`/api/student/grammar-drill/${encodeURIComponent(drillId)}`);
    } catch (e) {
      list.innerHTML = `<div style="color:#fca5a5; padding:12px; background:rgba(239,68,68,0.08); border-radius:8px; font-size:0.85rem;">⚠ ドリルを開けませんでした (${_gdEscape((e && (e.message || e)) || '')})</div>
        <div style="text-align:center; margin-top:10px;"><button type="button" data-gd-back="1" style="padding:7px 16px; background:rgba(255,255,255,0.06); color:#cbd5e1; border:1px solid rgba(255,255,255,0.15); border-radius:8px; cursor:pointer; font-size:0.82rem;">← 一覧に戻る</button></div>`;
      return;
    }
    const drill = (data && data.drill) || {};
    const questions = (data && data.questions) || [];
    const isCompleted = data.status === 'completed';
    const titleHtml = _gdRich(drill.title || '');
    const meta = [drill.unit, drill.level].filter(Boolean).map(x => _gdEscape(x)).join(' ・ ');

    if (isCompleted) {
      // 完了済み → 復習表示 (your_answer / answer / explanation)
      const sc = (data.score_correct != null && data.score_total != null)
        ? `${data.score_correct}/${data.score_total}` : '';
      const pct = (data.score_correct != null && data.score_total)
        ? Math.round((data.score_correct / data.score_total) * 100) : null;
      const blocks = questions.map(q => _gdRenderQuestionBlock(drillId, q, { review: true })).join('');
      list.innerHTML = `
        <div style="margin-bottom:12px;">
          <button type="button" data-gd-back="1" style="padding:7px 16px; background:rgba(255,255,255,0.06); color:#cbd5e1; border:1px solid rgba(255,255,255,0.15); border-radius:8px; cursor:pointer; font-size:0.82rem;">← 一覧に戻る</button>
        </div>
        <div style="margin-bottom:14px;">
          <div style="font-size:1.0rem; font-weight:800; color:#fff;">${titleHtml}</div>
          ${meta ? `<div style="font-size:0.8rem; color:#94a3b8; margin-top:3px;">${meta}</div>` : ''}
          <div style="margin-top:10px; padding:10px 14px; background:rgba(52,211,153,0.1); border:1px solid rgba(52,211,153,0.35); border-radius:10px; color:#6ee7b7; font-weight:bold; font-size:0.95rem;">✅ 完了済み スコア ${_gdEscape(sc)}${pct != null ? ` (${pct}%)` : ''}</div>
        </div>
        ${blocks}
        <div style="text-align:center; margin-top:6px;">
          <button type="button" data-gd-back="1" style="padding:8px 18px; background:rgba(255,255,255,0.06); color:#cbd5e1; border:1px solid rgba(255,255,255,0.15); border-radius:8px; cursor:pointer; font-size:0.85rem;">← 一覧に戻る</button>
        </div>`;
      _gdApplyKatex(list);
      return;
    }

    // 未完了 → 解答フォーム
    const blocks = questions.map(q => _gdRenderQuestionBlock(drillId, q, { review: false })).join('');
    list.innerHTML = `
      <div style="margin-bottom:12px;">
        <button type="button" data-gd-back="1" style="padding:7px 16px; background:rgba(255,255,255,0.06); color:#cbd5e1; border:1px solid rgba(255,255,255,0.15); border-radius:8px; cursor:pointer; font-size:0.82rem;">← 一覧に戻る</button>
      </div>
      <div style="margin-bottom:14px;">
        <div style="font-size:1.0rem; font-weight:800; color:#fff;">${titleHtml}</div>
        ${meta ? `<div style="font-size:0.8rem; color:#94a3b8; margin-top:3px;">${meta}</div>` : ''}
        <div style="font-size:0.78rem; color:#94a3b8; margin-top:6px;">全 ${questions.length} 問 — すべて答えてから「提出」を押してください。</div>
      </div>
      <div data-gd-form="${_gdEscape(String(drillId))}">${blocks}</div>
      <div data-gd-submit-msg style="text-align:center; color:#fca5a5; font-size:0.82rem; min-height:1.1em; margin-bottom:8px;"></div>
      <div style="text-align:center;">
        <button type="button" data-gd-submit="${_gdEscape(String(drillId))}" data-gd-total="${questions.length}" style="padding:11px 28px; background:linear-gradient(135deg,#14b8a6,#10b981); color:#fff; border:0; border-radius:10px; font-weight:bold; font-size:0.95rem; cursor:pointer; box-shadow:0 4px 12px rgba(20,184,166,0.3);">📤 提出して採点する</button>
      </div>`;
    _gdApplyKatex(list);
  }

  // 提出 (POST /api/student/grammar-drill/{id}/submit)
  // 🔰 コーチの今日の一手から診断ドリルを直接開くための公開フック (2026-06-11)
  window._gdOpenDrill = openDrill;
  window._gdReloadList = loadList;

  // 採点結果 → LB 復習カード同期 (誤答のみ新規カード化・正解は既存カードの前進のみ)
  function _gdSyncResultsToReview(res) {
    if (!window.LB || !window.LB.recordAttempt) return;
    const results = (res && res.results) || [];
    if (!results.length) return;
    let sid = 'guest';
    try {
      const s = JSON.parse(localStorage.getItem('ai_juku_session_student') || 'null');
      if (s && s.id != null) sid = s.id;
    } catch (_) { /* noop */ }
    const letters = ['A', 'B', 'C', 'D', 'E', 'F'];
    results.forEach(function (r) {
      try {
        const choices = Array.isArray(r.choices) ? r.choices : [];
        const problem = String(r.stem || '') + '\n' +
          choices.map(function (cTxt, i) { return '(' + (letters[i] || (i + 1)) + ') ' + cTxt; }).join('\n');
        const ci = (r.correct_answer == null) ? null : Number(r.correct_answer);
        const answer = (ci != null && letters[ci] ? '(' + letters[ci] + ') ' : '') + (ci != null ? (choices[ci] || '') : '');
        const key = ('英語__' + problem).slice(0, 200);
        if (!r.is_correct) {
          LB.recordAttempt(sid, {
            key: key,
            subject: '英語',
            topic: (r.unit || '英文法').toString(),
            problem: problem.slice(0, 1200),
            answer: answer,
            explanation: String(r.explanation || ''),
          }, false);
        } else {
          // 既存カード (過去に間違えた同一問題) のみ前進。
          // ⚠ LB.markCard はカード不在だと alert を出すため、存在を確認してから呼ぶ
          let exists = false;
          try {
            const cardsRaw = localStorage.getItem('ai_juku_lb__' + sid + '__cards');
            exists = !!(cardsRaw && JSON.parse(cardsRaw)[key]);
          } catch (_) { exists = false; }
          if (exists) LB.markCard(key, true, sid);
        }
      } catch (_) { /* 1 問の失敗で他を止めない */ }
    });
  }

  async function submitDrill(drillId, expectedTotal, btn) {
    const form = list.querySelector(`[data-gd-form="${CSS && CSS.escape ? CSS.escape(String(drillId)) : drillId}"]`)
      || list.querySelector('[data-gd-form]');
    const msgEl = list.querySelector('[data-gd-submit-msg]');
    const answers = {};
    if (form) {
      form.querySelectorAll('input[type="radio"]:checked').forEach(inp => {
        const qid = inp.getAttribute('data-gd-qid');
        if (qid != null) answers[qid] = Number(inp.value);
      });
    }
    const answeredN = Object.keys(answers).length;
    if (expectedTotal && answeredN < Number(expectedTotal)) {
      if (msgEl) msgEl.textContent = `⚠ 未回答の問題があります (${answeredN}/${expectedTotal})。すべて答えてください。`;
      return;
    }
    if (msgEl) msgEl.textContent = '';
    if (btn) { btn.disabled = true; btn.textContent = '⏳ 採点中...'; }
    let res;
    try {
      res = await slApiFetch(`/api/student/grammar-drill/${encodeURIComponent(drillId)}/submit`, {
        method: 'POST',
        body: JSON.stringify({ answers }),
      });
    } catch (e) {
      if (msgEl) msgEl.textContent = '❌ 提出に失敗しました: ' + ((e && (e.message || e)) || '');
      if (btn) { btn.disabled = false; btn.textContent = '📤 提出して採点する'; }
      return;
    }
    // 🔁 誤答→復習カード連携 (2026-06-11 塾長指示「自走に必要なもの②」):
    // 間違えた問題を LB (忘却曲線) に登録し翌日「今日の復習」に自動で出す。
    // 正解した問題は「過去に間違えてカード化済み」の場合のみ前進させる (正解問題で復習を埋めない)。
    // フレッシュ提出時のみ実行 (renderResult は完了済みドリルの再閲覧でも呼ばれるためここに置く)。
    try { _gdSyncResultsToReview(res); } catch (_) { /* best-effort */ }
    renderResult(drillId, res);
  }

  // 採点結果表示
  function renderResult(drillId, res) {
    const results = (res && res.results) || [];
    const correct = (res && res.score_correct != null) ? res.score_correct : 0;
    const total = (res && res.score_total != null) ? res.score_total : results.length;
    const pct = (res && res.percentage != null)
      ? res.percentage
      : (total ? Math.round((correct / total) * 100) : 0);
    const blocks = results.map(_gdRenderResultItem).join('');
    list.innerHTML = `
      <div style="margin-bottom:12px;">
        <button type="button" data-gd-back="1" style="padding:7px 16px; background:rgba(255,255,255,0.06); color:#cbd5e1; border:1px solid rgba(255,255,255,0.15); border-radius:8px; cursor:pointer; font-size:0.82rem;">← 一覧に戻る</button>
      </div>
      <div style="text-align:center; margin-bottom:16px; padding:16px; background:linear-gradient(135deg,rgba(20,184,166,0.14),rgba(16,185,129,0.1)); border:1px solid rgba(20,184,166,0.4); border-radius:12px;">
        <div style="font-size:0.85rem; color:#94a3b8; margin-bottom:4px;">採点結果</div>
        <div style="font-size:2rem; font-weight:800; color:#5eead4;">${_gdEscape(String(correct))} / ${_gdEscape(String(total))} <span style="font-size:1.1rem; color:#cbd5e1;">(${_gdEscape(String(pct))}%)</span></div>
        <div style="font-size:0.82rem; color:#cbd5e1; margin-top:6px;">${pct >= 80 ? '🎉 素晴らしい!' : pct >= 60 ? '👍 もう一歩!' : '📖 間違えた問題の解説を確認しましょう'}</div>
        ${res && res.unit === '診断' ? '<div style="font-size:0.8rem; color:#86efac; margin-top:8px; font-weight:700;">🔰 AI があなたの苦手を記録しました。明日からの「コーチの今日の一手」があなた専用になります</div>' : ''}
      </div>
      ${blocks}
      <div style="text-align:center; margin-top:6px;">
        <button type="button" data-gd-back="1" style="padding:9px 20px; background:rgba(255,255,255,0.06); color:#cbd5e1; border:1px solid rgba(255,255,255,0.15); border-radius:8px; cursor:pointer; font-size:0.85rem;">← 一覧に戻る</button>
      </div>`;
    _gdApplyKatex(list);
  }

  // イベント委譲 (一覧の行クリック / 戻る / 提出)
  list.addEventListener('click', (e) => {
    const t = e.target;
    if (!t || !t.closest) return;
    const back = t.closest('[data-gd-back]');
    if (back) { loadList(); return; }
    const submitBtn = t.closest('[data-gd-submit]');
    if (submitBtn) {
      const did = submitBtn.getAttribute('data-gd-submit');
      const total = submitBtn.getAttribute('data-gd-total');
      submitDrill(did, total, submitBtn);
      return;
    }
    const openEl = t.closest('[data-gd-open]');
    if (openEl) {
      const did = openEl.getAttribute('data-gd-open');
      if (did) openDrill(did);
      return;
    }
  });
  // キーボード操作 (一覧行の Enter/Space で開く)
  list.addEventListener('keydown', (e) => {
    if (e.key !== 'Enter' && e.key !== ' ') return;
    const openEl = e.target && e.target.closest && e.target.closest('[data-gd-open]');
    if (openEl) {
      e.preventDefault();
      const did = openEl.getAttribute('data-gd-open');
      if (did) openDrill(did);
    }
  });

  // 初期表示: 解答エリアは通常 非表示。ドリル一覧は宿題セクション(#homeworkSection)が描画し、
  // 「▶ 解いて提出する」で openDrill() がここを表示する (2026-06-16 ドリルを宿題に統合)。
  section.style.display = 'none';
}

// ==========================================================================
// 🧭 コーチの今日の一手 (2026-06-11 塾長指示: 低学力層オンボーディング)
//   課題: 機能が多く「何から始めればいいか分からない」生徒が何も始めずに離脱する
//   (実データ: 離脱者の 71% は機能利用ゼロ・「1回使って挫折」は 0%)。
//   解決: mypage 最上部に「今日はこれだけ」の単一 CTA を毎日 1 枚。優先順位は
//   決定論的ルール (AI 課金ゼロ): ①塾長の宿題ドリル → ②忘却曲線の復習カード →
//   ③弱点 TOP3 (kosei のみ) → ④学習記録 (対象プランのみ) → ⑤基礎レベル演習。
//   ✅達成で streak/XP が「実際に」増える (偽 seed 廃止とセットで本物の数字になる)。
// ==========================================================================
function _yesterdayKeyJST() {
  const jst = new Date(Date.now() + 9 * 60 * 60 * 1000 - 24 * 60 * 60 * 1000);
  return jst.toISOString().slice(0, 10);
}
function _cnmDoneKey() { return 'aj-cnm-done:' + mypageKeyForCurrentStudent(); }
function _cnmLastDoneKey() { return 'aj-cnm-last:' + mypageKeyForCurrentStudent(); }

async function initCoachNextMove(student, ajMode, isPreview) {
  const sec = document.getElementById('coachNextMove');
  if (!sec) return;
  const titleEl = document.getElementById('cnmTitle');
  const reasonEl = document.getElementById('cnmReason');
  const actionBtn = document.getElementById('cnmActionBtn');
  const doneBtn = document.getElementById('cnmDoneBtn');
  const doneMsg = document.getElementById('cnmDoneMsg');
  const streakChip = document.getElementById('cnmStreakChip');
  if (!titleEl || !reasonEl || !actionBtn || !doneBtn) return;

  function showSection() { sec.style.display = ''; }
  function setMove(move) {
    titleEl.textContent = move.title;
    reasonEl.textContent = move.reason;
    if (move.onClick) {
      // 一手がページ内アクション (診断開始等) の場合
      actionBtn.href = '#';
      actionBtn.onclick = function (e) { e.preventDefault(); move.onClick(actionBtn); };
    } else if (move.href) {
      actionBtn.href = move.href;
      actionBtn.onclick = null;
    } else if (move.scrollTo) {
      actionBtn.href = '#';
      actionBtn.onclick = function (e) {
        e.preventDefault();
        const t = document.getElementById(move.scrollTo);
        if (t) t.scrollIntoView({ behavior: 'smooth', block: 'start' });
      };
    }
    showSection();
  }
  function showDoneState() {
    titleEl.textContent = '✅ 今日のミッション達成！';
    reasonEl.textContent = 'よく頑張った！また明日、新しい一手を出すよ。';
    actionBtn.style.display = 'none';
    doneBtn.style.display = 'none';
    if (doneMsg) { doneMsg.style.display = ''; doneMsg.textContent = '🔥 この調子で毎日 1 つずつ積み上げよう'; }
    showSection();
  }

  // streak チップ (実データ・0 のときは出さない)
  try {
    const d0 = getMypageData();
    if (streakChip && (d0.streak || 0) > 0) {
      streakChip.textContent = '🔥 ' + d0.streak + ' 日連続';
      streakChip.style.display = '';
    }
  } catch (_) { /* noop */ }

  // 👁 塾長プレビュー: 実データを叩かず見た目サンプルのみ (生徒データ非表示の原則)
  if (isPreview) {
    setMove({ title: 'ドリル「仮定法」をやろう（サンプル表示）', reason: 'プレビュー用の表示例です。実際は宿題・復習・弱点データから自動で 1 つ選ばれます。', href: '#' });
    actionBtn.onclick = function (e) { e.preventDefault(); };
    doneBtn.style.opacity = '0.5';
    doneBtn.onclick = null;
    return;
  }

  // ✅ 達成ボタン: streak/XP を実際に進めて保存 (この経路が唯一の streak 加算 = 数字は本物)
  doneBtn.onclick = function () {
    let _tierUnlocked = false;
    try {
      const _tierBefore = _uiUnlockTier(getMypageData());
      localStorage.setItem(_cnmDoneKey(), todayKeyJST());
      const data = getMypageData();
      const last = localStorage.getItem(_cnmLastDoneKey());
      if (last === todayKeyJST()) { showDoneState(); return; }
      if (last === _yesterdayKeyJST()) data.streak = (data.streak || 0) + 1;
      else data.streak = 1;
      // streakHistory: 前回達成から空いた日数分 0 を詰めてから今日の 1 を積む (直近14日のみ保持)
      let hist = Array.isArray(data.streakHistory) ? data.streakHistory.slice() : [];
      if (last) {
        const gapDays = Math.max(0, Math.round((new Date(todayKeyJST()) - new Date(last)) / 86400000) - 1);
        for (let i = 0; i < Math.min(gapDays, 14); i++) hist.push(0);
      }
      hist.push(1);
      data.streakHistory = hist.slice(-14);
      data.xp = (data.xp || 0) + 50;
      localStorage.setItem(_cnmLastDoneKey(), todayKeyJST());
      saveMypageData(data);
      render(); // ヘッダーの streak/Lv./XP バーとアチーブメント・シンプルモード開放を実値で更新
      _tierUnlocked = _uiUnlockTier(data) > _tierBefore;
    } catch (_) { /* noop */ }
    showDoneState();
    // 🎉 開放 section は画面下方に出るため、達成メッセージで知らせる (review N4)
    if (_tierUnlocked && doneMsg) {
      doneMsg.textContent = '🎉 おめでとう！新しい機能が開放されたよ。下にスクロールして見てみよう';
    }
  };

  // 今日すでに達成済みなら達成状態で表示
  try {
    if (localStorage.getItem(_cnmDoneKey()) === todayKeyJST()) { showDoneState(); return; }
  } catch (_) { /* noop */ }

  const sid = student ? student.id : 'guest';

  // ① 塾長からの宿題ドリル (未完了があれば最優先)。やりかけのミニ診断もここで拾う
  let _drillItems = [];
  try {
    const d = await slApiFetch('/api/student/grammar-drills');
    _drillItems = (d && d.items) || [];
    const open = _drillItems.filter(function (it) { return it && it.status !== 'completed'; });
    if (open.length > 0) {
      const isDiag = open[0].unit === '診断';
      const unit = (open[0].unit || open[0].title || '').toString();
      const firstDrillId = open[0].drill_id;
      setMove({
        title: isDiag ? '🔰 はじめての実力チェック（10問・約3分）'
          : (unit ? 'ドリル「' + unit + '」をやろう' : '塾長からの宿題ドリルをやろう'),
        reason: isDiag
          ? 'やりかけの実力チェックが残っています。終わらせると AI があなたの苦手を見つけます。'
          : '塾長から出ている宿題が ' + open.length + ' 件あります。これを終わらせれば今日は OK！',
        // ドリルは宿題セクションに統合済み。一手から直接 解答エリアを開く (2026-06-16)。
        onClick: function () {
          if (firstDrillId != null && typeof window._gdOpenDrill === 'function') {
            window._gdOpenDrill(firstDrillId);
          } else {
            const sec = document.getElementById('homeworkSection') || document.getElementById('grammarDrillSection');
            if (sec) sec.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }
        },
      });
      return;
    }
  } catch (_) { /* 未配信/未対応プランは次のルールへ */ }

  // ② 復習カード (忘却曲線で今日が復習期限のもの)
  try {
    if (window.LB && typeof LB.getDueReviews === 'function') {
      const due = LB.getDueReviews(sid, 100) || [];
      if (due.length > 0) {
        setMove({
          title: '復習カードを ' + Math.min(due.length, 10) + ' 枚やろう',
          reason: '忘れかける今日のタイミングで見直すと、いちばん記憶に残ります。',
          scrollTo: 'lbTodayReview',
        });
        return;
      }
    }
  } catch (_) { /* noop */ }

  // ③ 弱点 TOP3 の 1 位 (大学受験モードのみ・データが溜まっている生徒)
  if (ajMode === 'kosei' && student && student.id != null) {
    try {
      const w = await slApiFetch('/api/student/weakness-top3?student_id=' + encodeURIComponent(sid) + '&limit=1&recommend_each=0');
      const top = ((w && w.weaknesses) || [])[0];
      if (top && (top.topic || top.subject)) {
        const label = (top.topic || top.subject).toString();
        // 🎯 [dojo-drill Phase2/2+ 2026-06-15 / review fix] バックエンドが reason・遅さから出し分けた
        //   recommended_action(label/hint/mode) を title/reason/href すべてで一貫して使う
        //   (片方だけ上書きすると三者矛盾が出るため・review fix #3)。理由データ無しの既定は
        //   mode='ai_tutor' なので従来の topic 深リンクが維持される (review fix #4)。
        const act = top.recommended_action || {};
        const useDrill = act.mode === 'drill';
        let reasonMsg = act.hint || '最近のミスから AI が見つけたあなたの弱点です。';
        if (top.low_confidence) {
          reasonMsg += '（まだ数問なので、もう少し解くと分析の精度が上がります）';
        }
        // 🎯 [習得クローズドループ 2026-06-17] 「習得(卒業)まであと何が必要か」を一手に明示
        if (top.mastery_hint) { reasonMsg += ' 🎯 ' + top.mastery_hint; }
        // 「正答だが遅い単元」は別枠 time_focus で明示 (本命の弱点と別単元なら一言添える・review fix #2)
        const tf = (w && w.time_focus) || null;
        if (tf && tf.topic && tf.topic !== (top.topic || '')) {
          reasonMsg += ' なお「' + tf.topic + '」は正答できていますが解くのが遅めです。時間配分も意識を。';
        }
        // これまで習得(卒業)した単元数をモチベ表示
        if (w && w.mastered_count > 0) { reasonMsg += ' ✅ これまで ' + w.mastered_count + ' 単元を習得済み。'; }
        const moveTitle = act.label
          ? ('苦手の 1 位「' + label + '」: ' + act.label)
          : ('苦手の 1 位「' + label + '」を 1 問だけ質問してみよう');
        // 🎯 ワンタップ演習: ドリル推奨ならその弱点単元の隙間ドリルを直接開く (?w_subject/w_topic で自動起動)
        const drillHref = 'dojo-drill.html?w_subject=' + encodeURIComponent(top.subject || '') + '&w_topic=' + encodeURIComponent(top.topic || '');
        setMove({
          title: moveTitle,
          reason: reasonMsg + (useDrill ? ' ⏱ この単元の隙間ドリルをすぐ開けます。' : ' 写真を撮って送るだけで 3 つの AI が解説します。'),
          href: useDrill ? drillHref : ('ai-tutor-photo.html?subject=' + encodeURIComponent(top.subject || '') + '&topic=' + encodeURIComponent(top.topic || '')),
        });
        return;
      }
      // 🎯 [習得クローズドループ 2026-06-17] 弱点が空 + 習得済みあり = 苦手を全クリア → 称賛して次の単元へ
      if (w && w.mastered_count > 0) {
        setMove({
          title: '🎉 苦手だった ' + w.mastered_count + ' 単元を習得！次の単元に挑戦しよう',
          reason: '記録された苦手をすべて基準クリアしました。新しい単元のドリルを解くと、また弱点を見つけて対策できます。',
          href: 'dojo-drill.html',
        });
        return;
      }
    } catch (_) { /* noop */ }
  }

  // ③.5 🔰 ミニ診断 (2026-06-11 塾長指示「自走に必要なもの③」): 弱点データが無い =
  // AI がまだその子を知らない状態なら、10 問の実力チェックを最初の一手にする。
  // 提出すると弱点が即時集計され、翌日からの一手・プリント推薦が個別化される。
  // 診断ドリルが既にある (open はルール①で拾済み / completed は再診断しない) 場合は出さない。
  if (ajMode === 'kosei' && student && student.id != null) {
    const _hasDiag = _drillItems.some(function (it) { return it && it.unit === '診断'; });
    if (!_hasDiag) {
      setMove({
        title: '🔰 はじめての実力チェック（10問・約3分）',
        reason: '10問だけ解くと、AI があなたの苦手な単元を見つけて、明日からの「一手」をあなた専用にします。',
        onClick: async function (btn) {
          // 🛡️ 二重クリックガード (review B1): <a> は disabled 不可のため dataset + pointerEvents で再入防止
          if (btn && btn.dataset.busy === '1') return;
          const _orig = btn ? btn.textContent : '';
          try {
            if (btn) { btn.dataset.busy = '1'; btn.style.pointerEvents = 'none'; btn.style.opacity = '0.6'; btn.textContent = '⏳ 問題を準備中...'; }
            const r = await slApiFetch('/api/student/diagnostic/start', { method: 'POST', body: '{}' });
            const sec2 = document.getElementById('grammarDrillSection');
            if (sec2) { sec2.style.display = 'block'; sec2.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
            if (r && r.drill_id && typeof window._gdOpenDrill === 'function') {
              window._gdOpenDrill(r.drill_id);
            } else if (typeof window._gdReloadList === 'function') {
              window._gdReloadList();
            }
          } catch (e) {
            // サーバの detail (例: 在庫不足は塾長連絡案内) があればそれを優先表示
            alert((e && e.message) ? String(e.message) : '診断の準備に失敗しました。少し待ってからもう一度お試しください。');
          } finally {
            if (btn) { btn.dataset.busy = ''; btn.style.pointerEvents = ''; btn.style.opacity = ''; btn.textContent = _orig || '▶ やってみる'; }
          }
        },
      });
      return;
    }
  }

  // ④ 学習記録 (対象プランのみ・データ上いちばん多い「最初の一歩」)
  try {
    const authStudent = (window.AuthGuard && window.AuthGuard.getStudent && window.AuthGuard.getStudent()) || student;
    if (authStudent && _canUseStudyMgmt(authStudent)) {
      setMove({
        title: '今日の勉強を 30 秒で記録しよう',
        reason: '続けて記録した人から伸びています。「⚡ 30分」ボタンを押すだけ！',
        scrollTo: 'study-log',
      });
      return;
    }
  } catch (_) { /* noop */ }

  // ⑤ fallback: 基礎レベル演習 (大学名を選ばず 1 タップで開始できる導線)
  if (ajMode === 'chugaku' || ajMode === 'shougaku') {
    setMove({
      title: 'AI の模試で実力チェックをしてみよう',
      reason: 'まずは今の実力を知るところから始めよう。',
      href: 'mock-exam.html',
    });
  } else {
    setMove({
      title: '英語の基礎問題に挑戦してみよう（共通テストレベル）',
      reason: '大学名はまだ選ばなくて OK。基礎〜標準レベルから AI が出題します。',
      href: 'english-exam.html?focus=daigaku&grade=kyotsu',
    });
  }
}


// ==========================================================================
// 🔰 シンプルモード Phase 2 (2026-06-11 塾長指示: 低学力層オンボーディング)
//   新規アカウント (created_at >= 導入日) のみ、mypage を基本機能だけに絞って開始。
//   ✅達成の積み上げ (xp) で段階開放: tier1 (3日分=150xp) → aj-adv1 表示 /
//   tier2 (7日分=350xp) → 全表示。「すべての機能を表示する」で手動切替もいつでも可 (永続)。
//   既存生徒 (created_at が導入日より前 or 取得不能) は何も変わらない (fail-safe = full)。
//   表示機構: body class (aj-hide-adv1/2) を外すだけ — 各 section は元の inline/JS 状態に
//   戻るため、JS の show/hide 制御と衝突しない (中学生モードと同じ思想)。
// ==========================================================================
const _UI_SIMPLE_CUTOFF = '2026-06-11'; // この日以降に作成されたアカウントのみシンプル開始
function _uiFullOverrideKey() { return 'aj-ui-full:' + mypageKeyForCurrentStudent(); }
function _uiTierSeenKey() { return 'aj-ui-tier-seen:' + mypageKeyForCurrentStudent(); }

function _uiSimpleEligible() {
  try {
    const s = (window.AuthGuard && window.AuthGuard.getStudent && window.AuthGuard.getStudent()) || null;
    if (!s || !s.created_at) return false; // created_at 不明 = 既存セッション → 全表示 (fail-safe)
    // 学習管理機能 (学習計画/カリキュラム/模試) を「購入済み」の生徒・コース生は対象外 (review N1)。
    // 買った中核機能を初日に隠さない + 2026-05-13「絶対に消えない」指示の section を購入者には隠さない。
    // ⚠ trial の plan は申込時の「希望プラン」(checkout のデフォルト radio = founder_special) が
    // 入るため、plan だけで除外すると主対象の新規体験生がほぼ全員対象外になる (review 指摘)。
    // → 除外は「購入済み (paid / past_due=猶予中の課金者) × _canUseStudyMgmt 該当プラン」に限定。
    if (s.course === 'kokuritsu_nankan') return false; // 国公立難関コース生は契約形態によらず全表示
    const _purchased = s.status === 'paid' || s.status === 'past_due';
    if (_purchased && _canUseStudyMgmt(s)) return false;
    const ca = String(s.created_at).slice(0, 10);
    return ca >= _UI_SIMPLE_CUTOFF;
  } catch (_) { return false; }
}
function _uiUnlockTier(data) {
  const xp = (data && data.xp) || 0;
  if (xp >= 350) return 2; // ✅ 7日分
  if (xp >= 150) return 1; // ✅ 3日分
  return 0;
}
// メール (週次プリント focus=worksheet) やアンカー直リンクが隠れ section を指す時は
// その訪問だけ全表示にして dead-end を防ぐ (review N3・永続化はしない)
function _uiDeepLinkWantsFull() {
  try {
    if (new URLSearchParams(window.location.search).get('focus') === 'worksheet') return true;
    const h = (window.location.hash || '').replace('#', '');
    if (!h) return false;
    const el = document.getElementById(h);
    return !!(el && el.closest && el.closest('section.aj-adv1, section.aj-adv2'));
  } catch (_) { return false; }
}

function applyUiLevel() {
  try {
    const body = document.body;
    // 塾長プレビュー: ?preview_ui=simple|simple1|simple2|full (preview_mode と独立・併用可)
    const pv = new URLSearchParams(window.location.search).get('preview_ui');
    let simple = false;
    let tier = 0;
    let transientFull = false;
    if (pv) {
      simple = pv.indexOf('simple') === 0;
      tier = pv === 'simple1' ? 1 : (pv === 'simple2' ? 2 : 0);
    } else if (_uiSimpleEligible()) {
      let manualFull = false;
      try { manualFull = localStorage.getItem(_uiFullOverrideKey()) === '1'; } catch (_) { /* noop */ }
      simple = !manualFull;
      tier = _uiUnlockTier(getMypageData());
      if (simple && tier < 2 && _uiDeepLinkWantsFull()) { tier = 2; transientFull = true; }
    }
    body.classList.toggle('aj-hide-adv1', simple && tier < 1);
    body.classList.toggle('aj-hide-adv2', simple && tier < 2);
    renderUiToggle(simple, tier, !!pv, transientFull);
  } catch (_) { /* 表示系のみ・失敗時は全表示のまま */ }
}

function renderUiToggle(simple, tier, isPreviewUi, transientFull) {
  const sec = document.getElementById('uiLevelToggle');
  const msg = document.getElementById('uiLevelMsg');
  const btn = document.getElementById('uiLevelBtn');
  if (!sec || !msg || !btn) return;
  const eligible = isPreviewUi || _uiSimpleEligible();
  if (!eligible) { sec.style.display = 'none'; return; }
  sec.style.display = '';
  // 残り日数は xp から動的計算 (review N5: 固定「3日/4日」は途中達成で不正確になる)
  let xp = 0;
  try { xp = (getMypageData().xp || 0); } catch (_) { /* noop */ }
  const daysTo = function (target) { return Math.max(1, Math.ceil((target - xp) / 50)); };
  // 🎉 新規開放の検知。preview / 一時全表示 (deep link) では seen を汚さない (review 指摘)
  let seen = 0;
  try { seen = parseInt(localStorage.getItem(_uiTierSeenKey()) || '0', 10) || 0; } catch (_) { /* noop */ }
  const newlyUnlocked = simple && !isPreviewUi && !transientFull && tier > seen;
  if (!isPreviewUi && !transientFull && tier > seen) {
    try { localStorage.setItem(_uiTierSeenKey(), String(tier)); } catch (_) { /* noop */ }
  }
  if (transientFull) {
    msg.textContent = '🔰 リンク先を表示するため、今回はすべての機能を表示しています';
    btn.style.display = 'none';
    return;
  }
  if (simple) {
    if (tier >= 2) {
      msg.textContent = (newlyUnlocked ? '🎉 全機能が開放されました！' : '🔰 全機能が開放済みです。') + 'これからも 1 日 1 つ積み上げよう';
      btn.style.display = 'none';
    } else if (tier === 1) {
      msg.textContent = (newlyUnlocked ? '🎉 配布プリント・弱点分析が開放されました！' : '🔰 シンプル表示中。') + '✅をあと ' + daysTo(350) + ' 日達成すると全機能が開放';
      btn.style.display = '';
      btn.textContent = 'すべての機能を表示する';
    } else {
      msg.textContent = '🔰 いまは基本機能だけを表示しています。✅をあと ' + daysTo(150) + ' 日達成すると新しい機能が開放！';
      btn.style.display = '';
      btn.textContent = 'すべての機能を表示する';
    }
  } else {
    msg.textContent = '全機能を表示中です。表示をシンプルに戻すこともできます';
    btn.style.display = '';
    btn.textContent = '🔰 シンプル表示に戻す';
  }
  if (isPreviewUi) { btn.onclick = null; btn.style.display = 'none'; return; }
  btn.onclick = function () {
    try {
      if (simple) localStorage.setItem(_uiFullOverrideKey(), '1');
      else localStorage.removeItem(_uiFullOverrideKey());
    } catch (_) { /* noop */ }
    applyUiLevel();
  };
}
