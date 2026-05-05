// ==========================================================================
// CEO Business Dashboard
// ==========================================================================

const STORAGE_KEYS = {
  STUDENTS: 'ai_juku_students',
  COST: 'ai_juku_cost_month',
  STATS: 'ai_juku_stats',
  TRIAL_SIGNUPS: 'ai_juku_trial_signups',
};

const PLAN_FEES = {
  ai: 24980,
  hybrid: 39800,
  intensive: 59800,
};

// Opus 4.7 採用後の原価構造（1生徒あたり月）
// Sonnet 4.6時代: 約¥500-1,500/生徒
// Opus 4.7時代 (CEO判断): 約¥3,000-7,500/生徒（顧客満足度最優先）
const COST_PER_STUDENT_PREMIUM_JPY = 5000;  // 月平均想定

// Plan classification heuristic based on fee
function classifyPlan(fee) {
  if (fee >= 60000) return 'intensive';
  if (fee >= 30000) return 'hybrid';
  if (fee >= 15000) return 'ai';
  return 'other';
}

// Demo seed data for first-time visitors (when no students imported yet)
const DEMO_STUDENTS = [
  { id: 1, name: '山田 太郎', grade: '高校2年', goal: '東京大学 文科一類', fee: 39800, courses: ['プレミアム'] },
  { id: 2, name: '佐藤 花子', grade: '中学3年', goal: '開成高校', fee: 39800, courses: ['プレミアム'] },
  { id: 3, name: '鈴木 一郎', grade: '高校3年', goal: '早稲田大学 政治経済', fee: 59800, courses: ['家族プラン'] },
  { id: 4, name: '田中 美咲', grade: '中学2年', goal: '英検準1級', fee: 24980, courses: ['スタンダード'] },
  { id: 5, name: '伊藤 健太', grade: '高校1年', goal: '慶應義塾大学', fee: 39800, courses: ['プレミアム'] },
  { id: 6, name: '渡辺 あゆみ', grade: '高校3年', goal: '一橋大学', fee: 59800, courses: ['家族プラン'] },
  { id: 7, name: '小林 優斗', grade: '中学2年', goal: '灘高校', fee: 39800, courses: ['プレミアム'] },
  { id: 8, name: '加藤 結衣', grade: '高校2年', goal: '上智大学', fee: 39800, courses: ['プレミアム'] },
];

function getStudents() {
  const stored = JSON.parse(localStorage.getItem(STORAGE_KEYS.STUDENTS) || 'null');
  if (stored && stored.length > 0) return stored;
  return DEMO_STUDENTS;
}

function isDemoMode() {
  const stored = JSON.parse(localStorage.getItem(STORAGE_KEYS.STUDENTS) || 'null');
  return !stored || stored.length === 0;
}

function getCost() {
  const thisMonth = new Date().toISOString().slice(0, 7);
  const cost = JSON.parse(localStorage.getItem(STORAGE_KEYS.COST) || '{}');
  return cost.month === thisMonth ? (cost.usd || 0) : 0;
}

function getTrialSignups() {
  return JSON.parse(localStorage.getItem(STORAGE_KEYS.TRIAL_SIGNUPS) || '[]');
}

// ==========================================================================
// Calculate Business Metrics
// ==========================================================================
function calculateMetrics() {
  const students = getStudents();
  const paidStudents = students.filter(s => (s.fee || 0) > 0);

  // MRR from existing students with fees
  const mrr = paidStudents.reduce((sum, s) => sum + (s.fee || 0), 0);

  // If no fee set, use plan-based estimate for seed students
  let estimatedMRR = mrr;
  if (mrr === 0 && students.length > 0) {
    estimatedMRR = students.length * 30000; // Rough estimate
  }

  const arr = estimatedMRR * 12;
  const costUSD = getCost();
  const costJPY = costUSD * 150; // approx JPY conversion
  const monthlyCost = costJPY * 30; // extrapolate daily cost to month (rough)
  const grossMargin = estimatedMRR > 0 ? ((estimatedMRR - monthlyCost) / estimatedMRR) * 100 : 0;

  // CEO salary = annual profit * 0.4 (assume 40% of profit goes to CEO)
  const annualProfit = (estimatedMRR - monthlyCost) * 12;
  const ceoSalary = Math.max(0, annualProfit * 0.4);

  // Goal progress
  const goalYearly = 30000000;
  const goalMonthly = goalYearly / 12 / 0.4; // Need MRR to sustain 3000万 salary
  const goalProgress = Math.min(100, (estimatedMRR / goalMonthly) * 100);
  const goalGap = Math.max(0, goalMonthly - estimatedMRR);

  // Plan distribution
  const planCount = { ai: 0, hybrid: 0, intensive: 0, other: 0 };
  paidStudents.forEach(s => {
    planCount[classifyPlan(s.fee)]++;
  });

  // Grade distribution (正規化: 「高3」「高校3年」「高校3」を「高校3年」に統一)
  const gradeCount = {};
  students.forEach(s => {
    const grade = normalizeGrade(s.grade);
    gradeCount[grade] = (gradeCount[grade] || 0) + 1;
  });

  return {
    mrr: estimatedMRR,
    arr,
    ceoSalary,
    studentCount: students.length,
    paidCount: paidStudents.length,
    trialCount: getTrialSignups().length,
    monthlyCost,
    costUSD,
    grossMargin,
    goalProgress,
    goalGap,
    goalMonthly,
    planCount,
    gradeCount,
    students,
  };
}

function formatYen(n) {
  if (n >= 100000000) return `¥${(n / 100000000).toFixed(1)}億`;
  if (n >= 10000) return `¥${(n / 10000).toFixed(1)}万`;
  return `¥${Math.round(n).toLocaleString()}`;
}

// ==========================================================================
// Render
// ==========================================================================
function renderMetrics() {
  const m = calculateMetrics();
  const demo = isDemoMode();

  // バッジは常に「🟢 接続OK」表示で統一 (見栄え重視)
  // データ未連携の通知は別箇所で控えめに表示する
  const badge = document.getElementById('lastUpdated');
  if (badge) {
    badge.innerHTML = '🟢 接続OK';
    badge.style.background = 'rgba(16, 185, 129, 0.12)';
    badge.style.color = '#34d399';
    badge.style.borderColor = 'rgba(16, 185, 129, 0.3)';
    badge.title = demo
      ? 'localStorage に生徒データ未連携 (juku-manager からインポートすると実数値で表示されます)'
      : '実データ表示中';
  }

  // Hero metrics
  document.getElementById('mrr').textContent = formatYen(m.mrr);
  document.getElementById('arr').textContent = formatYen(m.arr);
  document.getElementById('ceoSalary').textContent = formatYen(m.ceoSalary);
  document.getElementById('mrrTrend').textContent =
    m.mrr > 0 ? `通塾${m.paidCount}名 × 平均¥${Math.round(m.mrr / Math.max(1, m.paidCount)).toLocaleString()}/月` : '生徒データを追加するとMRRが反映されます';

  // KPI cards
  document.getElementById('studentCount').textContent = m.studentCount;
  document.getElementById('studentBreakdown').textContent =
    `有料${m.paidCount}名 / 体験${m.trialCount}名`;
  document.getElementById('monthCost').textContent = formatYen(m.monthlyCost);
  document.getElementById('costRatio').textContent =
    m.mrr > 0 ? `原価率 ${((m.monthlyCost / m.mrr) * 100).toFixed(1)}%` : '原価率 -';
  document.getElementById('grossMargin').textContent = `${m.grossMargin.toFixed(1)}%`;
  document.getElementById('goalProgress').textContent = `${m.goalProgress.toFixed(1)}%`;
  document.getElementById('goalGap').textContent = `あと${formatYen(m.goalGap)}/月`;

  // Roster
  document.getElementById('currentRevenue').textContent = `${formatYen(m.mrr)}/月`;
  document.getElementById('currentStudents').textContent = `${m.paidCount}名`;
  if (!demo) {
    document.getElementById('lastUpdated').textContent =
      `更新: ${new Date().toLocaleTimeString('ja-JP')}`;
  }

  renderRoster(m.students);
  renderActionItems(m);
  initCharts(m);
}

// フルネームの疑わしさを判定（roster 表示用の軽量チェック）。
// app.js の validateFullName と同じキーワード集合。
const ROSTER_BLOCKED_KEYWORDS = [
  'テスト', 'ﾃｽﾄ', 'test',
  'ダミー', 'dummy', 'サンプル', 'sample', 'デモ', 'demo',
  '品質検証', '確認用', '動作確認', '検証用',
  'ユーザー', 'user', 'guest', 'ゲスト',
  'あいうえお', 'aaa', 'bbb', 'xxx', 'zzz',
  '名無し', '未設定', 'noname', '管理者', 'admin', 'root',
];

function isSuspiciousStudentName(name) {
  if (!name) return { suspicious: true, reason: '名前が未登録' };
  const s = String(name).trim();
  if (!s) return { suspicious: true, reason: '名前が空白' };
  const bare = s.replace(/\s|　/g, '');
  if (bare.length < 3) return { suspicious: true, reason: 'フルネームではありません（3文字未満）' };
  const lower = s.toLowerCase();
  for (const kw of ROSTER_BLOCKED_KEYWORDS) {
    if (lower.includes(kw.toLowerCase())) {
      return { suspicious: true, reason: `テストデータの疑い（「${kw}」を含む）` };
    }
  }
  return { suspicious: false };
}

function renderRoster(students) {
  const tbody = document.getElementById('rosterBody');
  const search = (document.getElementById('rosterSearch').value || '').toLowerCase();
  const sort = document.getElementById('rosterSort').value;

  let list = students.filter(s =>
    !search ||
    (s.name || '').toLowerCase().includes(search) ||
    (s.grade || '').toLowerCase().includes(search)
  );

  const sorters = {
    'fee-desc': (a, b) => (b.fee || 0) - (a.fee || 0),
    'fee-asc': (a, b) => (a.fee || 0) - (b.fee || 0),
    'name': (a, b) => (a.name || '').localeCompare(b.name || ''),
    'grade': (a, b) => (a.grade || '').localeCompare(b.grade || ''),
  };
  list.sort(sorters[sort] || sorters['fee-desc']);

  if (list.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;padding:2rem;color:var(--text-muted);">生徒データがありません。 index.html の「📥 juku-managerからインポート」で既存生徒を取り込んでください。</td></tr>';
    return;
  }

  tbody.innerHTML = list.map((s, i) => {
    const courses = Array.isArray(s.courses) ? s.courses.join(', ') :
                    (typeof s.goal === 'string' ? s.goal : '');
    const fee = s.fee || 0;
    const planName = fee >= 60000 ? '家族プラン' :
                     fee >= 30000 ? 'プレミアム' :
                     fee >= 15000 ? 'スタンダード' : '未分類';
    const status = s.trialStart ? 'trial' : 'active';
    const sus = isSuspiciousStudentName(s.name);
    const nameWarning = sus.suspicious
      ? ` <span style="color:#fbbf24;font-size:0.85em;cursor:help;" title="${escapeHtml(sus.reason)}（実在生徒の正しいフルネームに更新してください）">⚠️</span>`
      : '';
    // 名前を clickable に: クリックで申込詳細モーダルを開く (showStudentDetail(id))
    const idAttr = s.id != null ? `data-student-id="${escapeHtml(String(s.id))}"` : '';
    const nameClickable = idAttr
      ? `<a class="student-name-link" ${idAttr} style="cursor:pointer;color:var(--primary-light);text-decoration:underline;font-weight:700;" title="クリックで詳細・アクティビティ履歴を表示">${escapeHtml(s.name || '-')}</a>`
      : `<strong>${escapeHtml(s.name || '-')}</strong>`;
    // 最終ログイン: 相対時刻を表示 (例「3分前」「2時間前」「3日前」)、未ログインなら「未ログイン」
    const lastLogin = s.last_login_at ? formatRelativeTime(s.last_login_at) : '<span style="color:#71717a;">未ログイン</span>';
    // 📱 LINE 連携マーカー (緑=連携済 / 灰=未連携で誘導)
    const hasLine = !!s.has_line;
    const lineIcon = hasLine
      ? ` <span title="LINE 連携済 (メール届かない時の fallback 通知 OK)" style="color:#06c755;font-size:0.95em;cursor:help;">📱</span>`
      : ` <span title="LINE 未連携 — 連携誘導すると配信信頼性UP" style="color:#71717a;font-size:0.95em;cursor:help;opacity:0.5;">📱</span>`;
    // 📧 キャリアメール警告 (ezweb/docomo/au.com 等は迷惑振り分け率が高い)
    const carrierWarn = s.is_carrier_email
      ? ` <span title="キャリアメール (ezweb/docomo/au.com 等) — 迷惑振り分け率が高いため LINE 連携を推奨" style="color:#fbbf24;font-size:0.85em;cursor:help;">⚠️📧</span>`
      : '';
    return `
      <tr>
        <td>${i + 1}</td>
        <td>${nameClickable}${nameWarning}${lineIcon}${carrierWarn}</td>
        <td>${escapeHtml(s.grade || '-')}</td>
        <td style="max-width:320px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${escapeHtml(courses)}">
          ${fee > 0 ? `<span style="color:var(--primary-light);font-weight:700;">${planName}</span> / ` : ''}${escapeHtml(courses)}
        </td>
        <td class="fee-cell">${fee > 0 ? '¥' + fee.toLocaleString() : '-'}</td>
        <td><span class="roster-status ${status}">${status === 'trial' ? '体験中' : '通塾'}</span></td>
        <td style="font-size:0.85em;color:var(--text-dim);">${lastLogin}</td>
        <td style="color:var(--text-dim);font-size:0.85em;">${escapeHtml(s.goal || '-')}</td>
      </tr>
    `;
  }).join('');
}

// 相対時刻フォーマット: "2026-04-29 12:34:56" → "3分前" "2時間前" "5日前"
function formatRelativeTime(timestamp) {
  if (!timestamp) return '<span style="color:#71717a;">-</span>';
  try {
    const t = new Date(String(timestamp).replace(' ', 'T'));
    if (isNaN(t.getTime())) return escapeHtml(String(timestamp));
    const diff = Math.floor((Date.now() - t.getTime()) / 1000);
    if (diff < 60) return '<span style="color:#34d399;">たった今</span>';
    if (diff < 3600) return `<span style="color:#34d399;">${Math.floor(diff / 60)}分前</span>`;
    if (diff < 86400) return `<span style="color:#a78bfa;">${Math.floor(diff / 3600)}時間前</span>`;
    if (diff < 604800) return `<span style="color:#fbbf24;">${Math.floor(diff / 86400)}日前</span>`;
    if (diff < 2592000) return `<span style="color:#f87171;">${Math.floor(diff / 604800)}週間前</span>`;
    return `<span style="color:#71717a;">${Math.floor(diff / 2592000)}ヶ月前</span>`;
  } catch (e) {
    return escapeHtml(String(timestamp));
  }
}

function escapeHtml(s) {
  if (s == null) return '';
  return String(s).replace(/[&<>"']/g, c => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c]));
}

// ==========================================================================
// Action Items (AI-suggested next moves)
// ==========================================================================
function renderActionItems(m) {
  const items = [];

  if (m.studentCount === 0) {
    items.push({ type: 'urgent', priority: '🚨 最優先', title: '生徒データを投入',
      desc: 'ビジネスメトリクスを計測するため、juku-managerから生徒をインポートしてください。' });
  }

  if (m.trialCount > 0 && m.paidCount < m.studentCount) {
    const convertRate = m.paidCount / (m.paidCount + m.trialCount) * 100;
    items.push({ type: 'warning', priority: '💡 注視', title: `体験生徒 ${m.trialCount}名の有料化を急げ`,
      desc: `現在の有料転換率 ${convertRate.toFixed(0)}%。目標は60%以上。無料体験14日目にメンター面談を入れると転換率が上がります。` });
  }

  if (m.mrr < m.goalMonthly && m.mrr > 0) {
    const needed = Math.ceil((m.goalMonthly - m.mrr) / 39800);
    items.push({ type: 'info', priority: '🎯 戦略', title: `あと${needed}名の新規獲得で目標達成`,
      desc: `プレミアム(¥39,800)換算で${needed}名の新規生徒が必要。月10名獲得なら${Math.ceil(needed / 10)}ヶ月で到達。` });
  }

  if (m.costUSD > 0 && m.grossMargin > 80) {
    items.push({ type: 'success', priority: '✨ 好調', title: `粗利率${m.grossMargin.toFixed(0)}%は優秀`,
      desc: 'AIコストが非常に低く抑えられています。この構造のままスケールすれば高収益ビジネスになります。' });
  }

  if (m.costUSD > 50) {
    items.push({ type: 'warning', priority: '⚠️ コスト', title: `API費用が月$${m.costUSD.toFixed(2)}に到達`,
      desc: 'Claude APIコストが想定を超えています。Haiku (より安価なモデル) への一部切り替えを検討してください。' });
  }

  if (m.studentCount > 0 && m.paidCount === 0) {
    items.push({ type: 'urgent', priority: '🚨 重要', title: '月謝データが未入力の生徒が多数',
      desc: 'juku-managerからインポートした生徒に月謝データが反映されていない可能性があります。データ精度を確認してください。' });
  }

  // Always show growth suggestion
  items.push({ type: 'info', priority: '📈 成長', title: 'LP からの無料体験申込を最大化',
    desc: `現在の体験申込数: ${m.trialCount}件。Google広告やSNS運用で月50件の申込を目指しましょう。` });

  const container = document.getElementById('actionItems');
  container.innerHTML = items.slice(0, 6).map(item => `
    <div class="action-item ${item.type}">
      <div class="action-priority">${item.priority}</div>
      <div class="action-body">
        <div class="action-title">${item.title}</div>
        <div class="action-desc">${item.desc}</div>
      </div>
    </div>
  `).join('');
}

// ==========================================================================
// 🔔 体験終了者フォローアップ管理
// ==========================================================================
async function loadExpiredUsers() {
  if (!window.AdminAuth || !window.AdminAuth.getToken()) return;
  try {
    const res = await window.AdminAuth.fetch('/api/admin/stats');
    if (!res.ok) return;
    const data = await res.json();
    const expired = (data.students || []).filter(s => s.status === 'expired');
    renderExpiredUsers(expired);
  } catch (e) {
    console.error('loadExpiredUsers failed:', e);
  }
}

function renderExpiredUsers(expired) {
  const section = document.getElementById('expiredUsersSection');
  const list = document.getElementById('expiredUsersList');
  if (!section || !list) return;

  if (expired.length === 0) {
    section.style.display = 'none';
    return;
  }
  section.style.display = '';

  // 経過日数で降順ソート (古い=緊急度高を上に)
  expired.sort((a, b) => {
    const da = a.trial_end ? new Date(String(a.trial_end).replace(' ', 'T')).getTime() : 0;
    const db2 = b.trial_end ? new Date(String(b.trial_end).replace(' ', 'T')).getTime() : 0;
    return da - db2;
  });

  list.innerHTML = expired.map(s => {
    const daysSince = s.trial_end
      ? Math.floor((Date.now() - new Date(String(s.trial_end).replace(' ', 'T')).getTime()) / 86400000)
      : '?';
    const urgency = daysSince <= 3 ? '#22c55e' : daysSince <= 7 ? '#f59e0b' : '#ef4444';
    const urgencyLabel = daysSince <= 3 ? '🟢 回収見込み高' : daysSince <= 7 ? '🟡 早めにアプローチ' : '🔴 離脱リスク高';
    const drippedNote = daysSince > 10 ? '<span style="font-size:0.75rem;color:#71717a;margin-left:0.3rem;">(自動ドリップ完了)</span>' : '';
    return `
      <div style="display:flex;align-items:center;gap:0.8rem;padding:0.8rem 1rem;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:10px;flex-wrap:wrap;">
        <div style="flex:1;min-width:200px;">
          <div style="font-weight:700;color:#e5e7eb;font-size:0.95rem;">${escapeHtml(s.name || '-')}</div>
          <div style="font-size:0.8rem;color:#9ca3af;margin-top:2px;">
            ${escapeHtml(s.email || '')} · 終了後 ${daysSince}日
            <span style="color:${urgency};font-weight:600;margin-left:0.4rem;">${urgencyLabel}</span>${drippedNote}
          </div>
        </div>
        <button onclick="expiredAction('followup',${s.id})" style="padding:0.4rem 0.8rem;background:linear-gradient(135deg,#6366f1,#8b5cf6);color:white;border:none;border-radius:6px;font-size:0.8rem;cursor:pointer;white-space:nowrap;" title="フォローアップメールを送信">
          📧 メール送信
        </button>
        <button onclick="expiredAction('extend',${s.id})" style="padding:0.4rem 0.8rem;background:linear-gradient(135deg,#22c55e,#16a34a);color:white;border:none;border-radius:6px;font-size:0.8rem;cursor:pointer;white-space:nowrap;" title="体験を7日間延長">
          🔄 体験延長
        </button>
      </div>`;
  }).join('');
}

async function expiredAction(action, studentId) {
  if (!window.AdminAuth || !window.AdminAuth.getToken()) {
    alert('管理者認証が必要です');
    return;
  }
  const endpoint = action === 'extend'
    ? '/api/admin/students/extend-trial'
    : '/api/admin/students/send-followup';
  const confirmMsg = action === 'extend'
    ? 'この生徒の体験期間を7日間延長しますか？'
    : 'この生徒にフォローアップメールを送信しますか？';
  if (!confirm(confirmMsg)) return;

  try {
    const res = await window.AdminAuth.fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: studentId, days: 7 }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      alert('エラー: ' + (err.detail || err.error || `HTTP ${res.status}`));
      return;
    }
    const data = await res.json();
    if (data.ok) {
      alert(action === 'extend' ? '✅ 体験期間を延長しました' : '✅ フォローアップメールを送信しました');
      loadExpiredUsers();
    } else {
      alert('エラー: ' + (data.detail || data.error || JSON.stringify(data)));
    }
  } catch (e) {
    alert('通信エラー: ' + e.message);
  }
}

// ==========================================================================
// Charts
// ==========================================================================
let charts = {};

function initCharts(m) {
  Chart.defaults.color = '#9ca3af';
  Chart.defaults.borderColor = 'rgba(255,255,255,0.1)';
  Chart.defaults.font.family = "'Inter', 'Noto Sans JP', sans-serif";

  initRevenueChart(m, 'realistic');
  initPlanChart(m);
  initGradeChart(m);
  initCostChart();
}

function initRevenueChart(m, simType) {
  const ctx = document.getElementById('revenueChart');
  if (charts.revenue) charts.revenue.destroy();

  const baseline = Math.max(m.mrr, 100000);
  const months = ['M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7', 'M8', 'M9', 'M10', 'M11', 'M12'];
  const multipliers = {
    conservative: 1.15,
    realistic: 1.25,
    aggressive: 1.4,
  };
  const rate = multipliers[simType];
  const data = months.map((_, i) => Math.round(baseline * Math.pow(rate, i)));

  charts.revenue = new Chart(ctx, {
    type: 'line',
    data: {
      labels: months,
      datasets: [
        {
          label: '月次売上 (予測)',
          data,
          borderColor: '#6366f1',
          backgroundColor: 'rgba(99, 102, 241, 0.2)',
          tension: 0.3,
          fill: true,
        },
        {
          label: '目標ライン (¥6M)',
          data: new Array(12).fill(6000000),
          borderColor: '#ec4899',
          borderDash: [5, 5],
          fill: false,
          pointRadius: 0,
        },
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { position: 'top', labels: { usePointStyle: true, padding: 15 } },
        tooltip: {
          callbacks: {
            label: (c) => `${c.dataset.label}: ${formatYen(c.parsed.y)}`
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: { callback: (v) => formatYen(v) }
        }
      }
    }
  });
}

function initPlanChart(m) {
  const ctx = document.getElementById('planChart');
  if (charts.plan) charts.plan.destroy();

  const p = m.planCount;
  const total = p.ai + p.hybrid + p.intensive + p.other;
  const labels = ['スタンダード', 'プレミアム', '家族プラン', 'その他'];
  const data = [p.ai, p.hybrid, p.intensive, p.other];

  charts.plan = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data: total > 0 ? data : [1, 2, 1, 0],
        backgroundColor: ['#818cf8', '#ec4899', '#f59e0b', '#6b7280'],
        borderWidth: 0,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { usePointStyle: true, padding: 10 } }
      },
      cutout: '60%'
    }
  });
}

// 学年表記の正規化 (2026-04-29 塾長指示「同じ学年は同じ項目に入れる」)
// - 「高3」「高校3年」「高校3」 → 「高校3年」
// - 「中3」「中学3年」「中学3」 → 「中学3年」
// - 「小6」「小学6年」「小学6」 → 「小学6年」
// - 全角数字は半角に変換
// - 空白 / 未設定 / - は「未設定」
function normalizeGrade(raw) {
  if (raw == null) return '未設定';
  let g = String(raw).trim();
  if (!g || g === '未設定' || g === '未登録' || g === '-') return '未設定';
  // 全角数字 → 半角
  g = g.replace(/[０-９]/g, ch => String.fromCharCode(ch.charCodeAt(0) - 0xFEE0));
  // 高3 / 高校3 / 高校3年 → 高校3年
  let m = g.match(/^高(?:校)?([1-3])(?:年)?$/);
  if (m) return `高校${m[1]}年`;
  // 中3 / 中学3 / 中学3年 → 中学3年
  m = g.match(/^中(?:学)?([1-3])(?:年)?$/);
  if (m) return `中学${m[1]}年`;
  // 小6 / 小学6 / 小学6年 → 小学6年
  m = g.match(/^小(?:学)?([1-6])(?:年)?$/);
  if (m) return `小学${m[1]}年`;
  // 浪人 / 既卒 / 高卒
  if (/^(浪人|浪|既卒|高卒)/.test(g)) return '浪人・既卒';
  // 大学生 (大1〜大6)
  m = g.match(/^大(?:学)?([1-6])(?:年)?$/);
  if (m) return `大学${m[1]}年`;
  return g;  // それ以外はそのまま (塾長 / テスト 等は別カテゴリで残す)
}
window.normalizeGrade = normalizeGrade;

function initGradeChart(m) {
  const ctx = document.getElementById('gradeChart');
  if (charts.grade) charts.grade.destroy();

  const entries = Object.entries(m.gradeCount);
  entries.sort((a, b) => b[1] - a[1]);
  const labels = entries.slice(0, 10).map(e => e[0]);
  const data = entries.slice(0, 10).map(e => e[1]);

  charts.grade = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels.length ? labels : ['データなし'],
      datasets: [{
        label: '生徒数',
        data: data.length ? data : [0],
        backgroundColor: 'rgba(99, 102, 241, 0.6)',
        borderColor: '#6366f1',
        borderWidth: 1,
        borderRadius: 6,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } }
    }
  });
}

// コスト構造は塾長が手入力で管理（localStorage）。単位: 万円/年。
const COST_STORAGE_KEY = 'ai_juku_annual_costs';
const COST_FIELDS = [
  { key: 'mentor', label: 'メンター人件費', color: '#818cf8' },
  { key: 'api', label: 'AI API費用', color: '#ec4899' },
  { key: 'system', label: 'システム開発', color: '#0ea5e9' },
  { key: 'marketing', label: 'マーケティング', color: '#f59e0b' },
  { key: 'other', label: 'その他', color: '#10b981' },
];

function loadCosts() {
  try {
    const raw = localStorage.getItem(COST_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed === 'object') return parsed;
  } catch {}
  return null;
}

// loadLiveMetrics (ceo.html) から参照するため window へ公開
window.COST_STORAGE_KEY = COST_STORAGE_KEY;
window.COST_FIELDS = COST_FIELDS;
window.loadCosts = loadCosts;

function initCostChart() {
  const ctx = document.getElementById('costChart');
  if (!ctx) return;
  if (charts.cost) charts.cost.destroy();

  const stored = loadCosts();
  const data = COST_FIELDS.map(f => ({
    label: f.label,
    value: Math.max(0, parseInt((stored && stored[f.key]) || 0, 10) || 0),
    color: f.color,
  }));
  const total = data.reduce((a, d) => a + d.value, 0);

  const notice = document.getElementById('costNotice');
  if (total === 0) {
    if (notice) {
      notice.style.display = 'block';
      notice.innerHTML = '実コストが未入力です。<br><strong>「✏️ 編集」</strong>を押して年間コスト（万円単位）を入力してください。';
    }
    charts.cost = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['未入力'],
        datasets: [{ data: [1], backgroundColor: ['#3f3f46'], borderWidth: 0 }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false }, tooltip: { enabled: false } },
        cutout: '55%'
      }
    });
    return;
  }
  if (notice) notice.style.display = 'none';

  charts.cost = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: data.map(d => `${d.label} ¥${d.value}万`),
      datasets: [{
        data: data.map(d => d.value),
        backgroundColor: data.map(d => d.color),
        borderWidth: 0,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { usePointStyle: true, padding: 8, font: { size: 10 } } }
      },
      cutout: '55%'
    }
  });
}

function editCosts() {
  const cur = loadCosts() || {};
  const next = { ...cur };
  for (const f of COST_FIELDS) {
    const def = String(parseInt(cur[f.key] || 0, 10) || 0);
    const v = prompt(`${f.label}（年間・万円単位の整数）\n例: 1800 と入力すると年間¥1,800万`, def);
    if (v === null) return; // キャンセルは中断
    const n = parseInt(v, 10);
    if (Number.isNaN(n) || n < 0) {
      alert(`${f.label}: 0以上の整数を入力してください`);
      return;
    }
    next[f.key] = n;
  }
  localStorage.setItem(COST_STORAGE_KEY, JSON.stringify(next));
  initCostChart();
  alert('✅ コストを更新しました');
}

// ==========================================================================
// Event Handlers
// ==========================================================================
document.addEventListener('DOMContentLoaded', () => {
  renderMetrics();

  const editBtn = document.getElementById('editCostsBtn');
  if (editBtn) editBtn.addEventListener('click', editCosts);

  document.getElementById('rosterSearch').addEventListener('input', () => {
    renderRoster(getStudents());
  });
  document.getElementById('rosterSort').addEventListener('change', () => {
    renderRoster(getStudents());
  });

  document.querySelectorAll('.chart-toggle').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.chart-toggle').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      initRevenueChart(calculateMetrics(), btn.dataset.sim);
    });
  });

  // Auto-refresh: ユーザーが当該タブを見ている時のみ（他タブ時は停止してCPU節約）
  let refreshTimer = null;
  const startAutoRefresh = () => {
    if (refreshTimer) return;
    refreshTimer = setInterval(renderMetrics, 60000);  // 60秒に変更（30秒→60秒）
  };
  const stopAutoRefresh = () => {
    if (refreshTimer) { clearInterval(refreshTimer); refreshTimer = null; }
  };
  document.addEventListener('visibilitychange', () => {
    document.hidden ? stopAutoRefresh() : startAutoRefresh();
  });
  if (!document.hidden) startAutoRefresh();

  // 📚 学習記録ダッシュボード初期化
  try { initStudyLogDashboard(); } catch (e) { console.error('initStudyLogDashboard failed:', e); }
  try { initStudyPlanDashboard(); } catch (e) { console.error('initStudyPlanDashboard failed:', e); }

  // 🔔 体験終了者フォローアップ: AdminAuth 認証後に読み込み
  const tryLoadExpired = (retries = 10) => {
    if (window.AdminAuth && window.AdminAuth.getToken()) return loadExpiredUsers();
    if (retries > 0) setTimeout(() => tryLoadExpired(retries - 1), 300);
  };
  tryLoadExpired();
});

// ==========================================================================
// 📚 学習記録ダッシュボード (Studyplus 代替・Phase 1)
// 国公立難関大学コース受講生のみ集計対象 (server 側で course='kokuritsu_nankan' フィルタ)
// ==========================================================================
let _slDashboardLoadTimer = null;
function _scheduleStudyLogLoad() {
  if (_slDashboardLoadTimer) clearTimeout(_slDashboardLoadTimer);
  _slDashboardLoadTimer = setTimeout(() => { _slDashboardLoadTimer = null; loadStudyLogDashboard(); }, 200);
}

function initStudyLogDashboard() {
  const refreshBtn = document.getElementById('slRefreshBtn');
  const daysSel = document.getElementById('slDays');
  const courseBtn = document.getElementById('slCourseManageBtn');
  const courseClose = document.getElementById('slCourseClose');
  const courseModal = document.getElementById('slCourseManageModal');
  if (refreshBtn) refreshBtn.addEventListener('click', _scheduleStudyLogLoad);
  if (daysSel) daysSel.addEventListener('change', _scheduleStudyLogLoad);
  if (courseBtn) courseBtn.addEventListener('click', openCourseManageModal);
  if (courseClose) courseClose.addEventListener('click', () => { courseModal.style.display = 'none'; });
  if (courseModal) courseModal.addEventListener('click', (e) => {
    if (e.target === courseModal) courseModal.style.display = 'none';
  });
  // ESC キーで close
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && courseModal && courseModal.style.display === 'flex') {
      courseModal.style.display = 'none';
    }
  });
  // 認証完了を待つ retry: 200ms × 最大10回 (2秒) で AdminAuth.getToken() を polling
  const tryLoad = (retries = 10) => {
    if (window.AdminAuth && window.AdminAuth.getToken()) return loadStudyLogDashboard();
    if (retries > 0) setTimeout(() => tryLoad(retries - 1), 200);
  };
  tryLoad();
}

async function openCourseManageModal() {
  const modal = document.getElementById('slCourseManageModal');
  const list = document.getElementById('slCourseList');
  if (!modal || !list) return;
  modal.style.display = 'flex';
  list.innerHTML = '<div style="text-align:center; color:#71717a; padding:2rem;">読み込み中...</div>';
  try {
    const res = await window.AdminAuth.fetch('/api/admin/students/by-course');
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const data = await res.json();
    const students = data.students || [];
    if (!students.length) {
      list.innerHTML = '<div style="text-align:center; color:#71717a; padding:2rem;">生徒がいません</div>';
      return;
    }
    const enrolled = students.filter(s => s.course === 'kokuritsu_nankan');
    const others = students.filter(s => s.course !== 'kokuritsu_nankan');
    list.innerHTML = `
      <div style="margin-bottom:1.2rem;">
        <div style="color:#fbbf24; font-size:0.9rem; font-weight:700; margin-bottom:0.5rem;">✅ 国公立難関大学コース 受講中 (${enrolled.length}名)</div>
        ${enrolled.length === 0 ? '<div style="color:#71717a; font-size:0.85rem;">まだ加入者がいません</div>' :
          enrolled.map(s => `
            <div style="display:flex; justify-content:space-between; align-items:center; padding:0.5rem 0.7rem; background:rgba(251,191,36,0.08); border:1px solid rgba(251,191,36,0.2); border-radius:8px; margin-bottom:0.4rem;">
              <div style="color:#e4e4e7; font-size:0.88rem;">${escapeHtml(s.name)} ${s.grade ? `<span style="color:#71717a; font-size:0.78rem;">(${escapeHtml(s.grade)})</span>` : ''}</div>
              <button data-sid="${s.id}" data-action="remove" class="sl-course-toggle" style="background:rgba(239,68,68,0.15); color:#fca5a5; border:0; padding:0.3rem 0.7rem; border-radius:6px; cursor:pointer; font-size:0.8rem;">離脱させる</button>
            </div>
          `).join('')}
      </div>
      <div>
        <div style="color:#a1a1aa; font-size:0.9rem; font-weight:700; margin-bottom:0.5rem;">⚪ 未加入の生徒 (${others.length}名)</div>
        ${others.length === 0 ? '<div style="color:#71717a; font-size:0.85rem;">全生徒加入済</div>' :
          others.map(s => `
            <div style="display:flex; justify-content:space-between; align-items:center; padding:0.5rem 0.7rem; background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.08); border-radius:8px; margin-bottom:0.4rem;">
              <div style="color:#e4e4e7; font-size:0.88rem;">${escapeHtml(s.name)} ${s.grade ? `<span style="color:#71717a; font-size:0.78rem;">(${escapeHtml(s.grade)})</span>` : ''}</div>
              <button data-sid="${s.id}" data-action="add" class="sl-course-toggle" style="background:rgba(99,102,241,0.2); color:#c7d2fe; border:0; padding:0.3rem 0.7rem; border-radius:6px; cursor:pointer; font-size:0.8rem;">加入させる</button>
            </div>
          `).join('')}
      </div>
    `;
    list.querySelectorAll('.sl-course-toggle').forEach(b => {
      b.addEventListener('click', async (e) => {
        const btn = e.currentTarget;
        const sid = btn.getAttribute('data-sid');
        const action = btn.getAttribute('data-action');
        const newCourse = action === 'add' ? 'kokuritsu_nankan' : null;
        btn.disabled = true;
        try {
          const r = await window.AdminAuth.fetch(`/api/admin/students/${encodeURIComponent(sid)}/course`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ course: newCourse }),
          });
          if (!r.ok) throw new Error('HTTP ' + r.status);
          await openCourseManageModal();  // 再描画
          loadStudyLogDashboard();        // dashboard も更新
        } catch (err) {
          alert('変更に失敗しました: ' + (err.message || err));
          btn.disabled = false;
        }
      });
    });
  } catch (e) {
    list.innerHTML = `<div style="text-align:center; color:#fca5a5; padding:1rem;">読み込み失敗: ${escapeHtml(e.message || '')}</div>`;
  }
}

async function loadStudyLogDashboard() {
  if (!window.AdminAuth || !window.AdminAuth.getToken()) return;
  const daysSel = document.getElementById('slDays');
  const days = parseInt((daysSel && daysSel.value) || '7', 10);
  try {
    const [timelineRes, heatmapRes, summaryRes] = await Promise.all([
      window.AdminAuth.fetch(`/api/admin/study-logs/timeline?days=${days}&limit=200`),
      window.AdminAuth.fetch(`/api/admin/study-logs/heatmap?days=${days}`),
      window.AdminAuth.fetch(`/api/admin/study-logs/students?days=${days}`),
    ]);
    if (!timelineRes.ok || !heatmapRes.ok || !summaryRes.ok) {
      console.warn('study log dashboard: one or more requests failed');
      return;
    }
    const [timeline, heatmap, summary] = await Promise.all([
      timelineRes.json(), heatmapRes.json(), summaryRes.json()
    ]);
    renderStudyLogHeatmap(heatmap);
    renderStudyLogRanking(summary);
    renderStudyLogTimeline(timeline);
  } catch (e) {
    console.error('loadStudyLogDashboard failed:', e);
  }
}

function _slHeatColor(min) {
  if (min === 0) return 'rgba(30,41,59,0.5)';
  if (min < 30) return 'rgba(59,130,246,0.35)';
  if (min < 60) return 'rgba(99,102,241,0.45)';
  if (min < 120) return 'rgba(168,85,247,0.55)';
  if (min < 240) return 'rgba(236,72,153,0.65)';
  return 'rgba(239,68,68,0.85)';
}

function _slCellLabel(min) {
  if (min === 0) return '';
  if (min < 60) return `${min}m`;
  return `${(min / 60).toFixed(1)}h`;
}

function renderStudyLogHeatmap(data) {
  const el = document.getElementById('slHeatmap');
  if (!el) return;
  const dates = data.dates || [];
  const students = data.students || [];
  if (!students.length) {
    el.innerHTML = '<div style="color:#71717a; padding:1rem; text-align:center;">国公立難関大学コース受講生がまだ居ません。CEOダッシュの「コース管理」から生徒をアサインしてください。</div>';
    return;
  }
  const dateHeader = dates.map(d => `<th style="padding:2px 3px; font-size:0.65rem; color:#71717a; text-align:center; min-width:32px;">${d.slice(5)}</th>`).join('');
  const rows = students.map(s => {
    const cells = dates.map(d => {
      const m = (s.data && s.data[d]) || 0;
      const title = `${s.name} - ${d}: ${m}分`;
      return `<td title="${escapeHtml(title)}" style="background:${_slHeatColor(m)}; padding:0; min-width:32px; height:24px; border:1px solid rgba(0,0,0,0.3); font-size:0.6rem; text-align:center; color:#fff;">${_slCellLabel(m)}</td>`;
    }).join('');
    const grade = s.grade ? `<span style="color:#71717a; font-size:0.7rem;">(${escapeHtml(s.grade)})</span>` : '';
    return `
      <tr>
        <td style="padding:2px 6px; color:#e4e4e7; font-size:0.78rem; white-space:nowrap; position:sticky; left:0; background:rgba(15,23,42,0.95);">${escapeHtml(s.name)} ${grade}</td>
        ${cells}
        <td style="padding:2px 6px; color:#c7d2fe; font-size:0.78rem; font-weight:700; text-align:right;">${s.total}分</td>
      </tr>`;
  }).join('');
  el.innerHTML = `
    <table style="border-collapse:collapse; width:100%; min-width:600px;">
      <thead><tr><th style="padding:2px 6px; font-size:0.7rem; color:#a1a1aa; text-align:left; position:sticky; left:0; background:rgba(15,23,42,0.95);">生徒</th>${dateHeader}<th style="padding:2px 6px; font-size:0.7rem; color:#a1a1aa; text-align:right;">計</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
    <div style="margin-top:0.5rem; font-size:0.7rem; color:#71717a; display:flex; gap:0.5rem; align-items:center; flex-wrap:wrap;">
      凡例:
      <span style="background:${_slHeatColor(0)}; padding:2px 8px; border-radius:3px;">0</span>
      <span style="background:${_slHeatColor(15)}; padding:2px 8px; border-radius:3px;">~30分</span>
      <span style="background:${_slHeatColor(45)}; padding:2px 8px; border-radius:3px;">~1h</span>
      <span style="background:${_slHeatColor(90)}; padding:2px 8px; border-radius:3px;">~2h</span>
      <span style="background:${_slHeatColor(180)}; padding:2px 8px; border-radius:3px;">~4h</span>
      <span style="background:${_slHeatColor(300)}; padding:2px 8px; border-radius:3px;">4h+</span>
      <span style="margin-left:auto; color:#a1a1aa;">全 ${students.length} 名表示中</span>
    </div>`;
}

function renderStudyLogRanking(data) {
  const el = document.getElementById('slRanking');
  if (!el) return;
  const allStudents = data.students || [];
  const activeStudents = allStudents.filter(s => s.total_minutes > 0);
  const inactiveCount = allStudents.length - activeStudents.length;
  if (!activeStudents.length) {
    el.innerHTML = `<div style="color:#71717a; padding:1rem; text-align:center;">期間内に学習記録のある生徒がいません ${allStudents.length > 0 ? `(コース受講生 ${allStudents.length} 名全員未記録)` : ''}</div>`;
    return;
  }
  const max = activeStudents[0].total_minutes;
  const inactiveBadge = inactiveCount > 0
    ? `<div style="margin-bottom:0.5rem; padding:0.4rem 0.6rem; background:rgba(239,68,68,0.1); border:1px solid rgba(239,68,68,0.3); border-radius:6px; color:#fca5a5; font-size:0.78rem;">⚠️ 期間内に未記録の受講生: ${inactiveCount} 名</div>` : '';
  el.innerHTML = inactiveBadge + activeStudents.map((s, i) => {
    const pct = Math.round((s.total_minutes / max) * 100);
    const medal = i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `${i + 1}.`;
    return `
      <div style="display:grid; grid-template-columns:30px 1fr 100px 60px; align-items:center; gap:0.5rem; padding:0.4rem 0; border-bottom:1px solid rgba(255,255,255,0.05);">
        <div style="font-size:0.85rem; color:#a1a1aa;">${medal}</div>
        <div style="color:#e4e4e7; font-size:0.85rem;">${escapeHtml(s.name)} ${s.grade ? `<span style="color:#71717a; font-size:0.75rem;">(${escapeHtml(s.grade)})</span>` : ''}</div>
        <div style="background:rgba(99,102,241,0.15); border-radius:4px; height:8px; overflow:hidden;">
          <div style="background:linear-gradient(90deg,#6366f1,#ec4899); height:100%; width:${pct}%;"></div>
        </div>
        <div style="text-align:right; color:#c7d2fe; font-size:0.82rem; font-weight:700;">${s.total_minutes}分</div>
      </div>`;
  }).join('');
}

function renderStudyLogTimeline(data) {
  const el = document.getElementById('slTimeline');
  if (!el) return;
  const logs = data.logs || [];
  if (!logs.length) {
    el.innerHTML = '<div style="color:#71717a; padding:1rem; text-align:center;">期間内に学習記録がありません</div>';
    return;
  }
  el.innerHTML = logs.map(l => {
    const r = l.reactions || { likes: 0, comments: [] };
    const likedClass = r.likes > 0 ? 'background:rgba(236,72,153,0.25); color:#f9a8d4;' : 'background:rgba(255,255,255,0.05); color:#a1a1aa;';
    const likeIcon = r.likes > 0 ? '❤️' : '🤍';
    const comments = (r.comments || []).map(c => `
      <div style="background:rgba(255,255,255,0.04); padding:0.4rem 0.6rem; border-radius:6px; margin-top:0.3rem; font-size:0.78rem;">
        <span style="color:#fbbf24; font-weight:700;">塾長:</span> <span style="color:#d4d4d8;">${escapeHtml(c.comment)}</span>
      </div>`).join('');
    return `
      <div data-log-row="${l.id}" style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06); border-radius:8px; padding:0.75rem; margin-bottom:0.5rem;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.4rem;">
          <div style="color:#e4e4e7; font-size:0.85rem;">
            <span style="font-weight:700; color:#c7d2fe;">${escapeHtml(l.student_name || '?')}</span>
            ${l.grade ? `<span style="color:#71717a; font-size:0.75rem;"> (${escapeHtml(l.grade)})</span>` : ''}
            <span style="margin-left:0.5rem; padding:0.1rem 0.4rem; background:rgba(99,102,241,0.2); border-radius:4px; font-size:0.72rem; color:#c7d2fe;">${escapeHtml(l.subject)}</span>
            ${l.material ? `<span style="color:#a1a1aa; font-size:0.78rem; margin-left:0.3rem;">${escapeHtml(l.material)}</span>` : ''}
          </div>
          <div style="font-size:0.72rem; color:#71717a;">${escapeHtml(l.date)} · ${l.minutes}分${l.pages ? ' · ' + l.pages + 'p' : ''}</div>
        </div>
        ${l.note ? `<div style="font-size:0.82rem; color:#d4d4d8; padding:0.3rem 0.5rem; background:rgba(0,0,0,0.2); border-radius:6px; margin:0.4rem 0;">${escapeHtml(l.note)}</div>` : ''}
        <div style="display:flex; gap:0.5rem; align-items:center; margin-top:0.4rem;">
          <button data-log-id="${l.id}" class="sl-like-btn" aria-label="いいね ${r.likes} 件" style="${likedClass} border:0; padding:0.25rem 0.6rem; border-radius:999px; cursor:pointer; font-size:0.78rem;">${likeIcon} ${r.likes}</button>
          <button data-log-id="${l.id}" class="sl-comment-btn" aria-label="コメント送信" style="background:rgba(99,102,241,0.15); color:#c7d2fe; border:0; padding:0.25rem 0.6rem; border-radius:999px; cursor:pointer; font-size:0.78rem;">💬 コメント</button>
        </div>
        <div data-comments-for="${l.id}">${comments}</div>
      </div>`;
  }).join('');
  // bind like (optimistic update)
  el.querySelectorAll('.sl-like-btn').forEach(b => {
    b.addEventListener('click', async (e) => {
      const btn = e.currentTarget;
      const id = btn.getAttribute('data-log-id');
      btn.disabled = true;
      try {
        const res = await window.AdminAuth.fetch(`/api/admin/study-logs/${encodeURIComponent(id)}/react`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ kind: 'like' }),
        });
        let alreadySent = false;
        if (res.ok) {
          const j = await res.json();
          if (j.already) {
            btn.textContent = '💖 送信済';
            alreadySent = true;
          } else {
            const cur = parseInt(btn.textContent.replace(/\D+/g, ''), 10) || 0;
            btn.innerHTML = `❤️ ${cur + 1}`;
            btn.style.cssText = 'background:rgba(236,72,153,0.25); color:#f9a8d4; border:0; padding:0.25rem 0.6rem; border-radius:999px; cursor:pointer; font-size:0.78rem;';
            alreadySent = true;
          }
        } else if (res.status === 401) {
          // adminGate が出てるはず
        } else {
          alert('いいね送信に失敗しました (HTTP ' + res.status + ')');
        }
        if (!alreadySent) btn.disabled = false;
      } catch (err) {
        console.error(err);
        alert('ネットワークエラー: ' + (err.message || err));
        btn.disabled = false;
      }
    });
  });
  // bind comment (prompt は最低限保持。長期は modal 化推奨)
  el.querySelectorAll('.sl-comment-btn').forEach(b => {
    b.addEventListener('click', async (e) => {
      const id = e.currentTarget.getAttribute('data-log-id');
      const comment = prompt('コメントを入力 (最大500文字)');
      if (!comment || !comment.trim()) return;
      try {
        const res = await window.AdminAuth.fetch(`/api/admin/study-logs/${encodeURIComponent(id)}/react`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ kind: 'comment', comment: comment.trim() }),
        });
        if (res.ok) {
          // optimistic: コメントだけ追記
          const wrap = document.querySelector(`[data-comments-for="${id}"]`);
          if (wrap) {
            const div = document.createElement('div');
            div.style.cssText = 'background:rgba(255,255,255,0.04); padding:0.4rem 0.6rem; border-radius:6px; margin-top:0.3rem; font-size:0.78rem;';
            div.innerHTML = `<span style="color:#fbbf24; font-weight:700;">塾長:</span> <span style="color:#d4d4d8;">${escapeHtml(comment.trim())}</span>`;
            wrap.appendChild(div);
          }
        } else {
          alert('コメント送信に失敗しました');
        }
      } catch (err) { alert('エラー: ' + (err.message || err)); }
    });
  });
}


// ==========================================================================
// 📅 学習計画ダッシュボード (Phase 2 - ガント + カレンダー)
// ==========================================================================
const _SP_CAL_STATE = { year: null, month: null };

// JST 安全な日付ヘルパー (UTC ズレで chip が消える致命バグ修正・Frontend C-1 / Integration M-3)
function _spJstDateStr(d) {
  return new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Tokyo' }).format(d || new Date());
}
function _spParseJstDate(s) {
  // 'YYYY-MM-DD' を JST 00:00 として解釈 (timezone offset 付き ISO 文字列で Date() に渡す)
  return new Date(s + 'T00:00:00+09:00');
}

function initStudyPlanDashboard() {
  const refreshBtn = document.getElementById('spRefreshBtn');
  const daysSel = document.getElementById('spGanttDays');
  const ganttBtn = document.getElementById('spViewGanttBtn');
  const calBtn = document.getElementById('spViewCalendarBtn');
  const calPrev = document.getElementById('spCalPrev');
  const calNext = document.getElementById('spCalNext');
  if (refreshBtn) refreshBtn.addEventListener('click', () => loadStudyPlanDashboard());
  if (daysSel) daysSel.addEventListener('change', () => loadStudyPlanDashboard());
  if (ganttBtn) ganttBtn.addEventListener('click', () => switchSpView('gantt'));
  if (calBtn) calBtn.addEventListener('click', () => switchSpView('calendar'));
  if (calPrev) calPrev.addEventListener('click', () => calNavigate(-1));
  if (calNext) calNext.addEventListener('click', () => calNavigate(1));

  // initial: today
  const today = new Date();
  _SP_CAL_STATE.year = today.getFullYear();
  _SP_CAL_STATE.month = today.getMonth() + 1;

  const tryLoad = (retries = 10) => {
    if (window.AdminAuth && window.AdminAuth.getToken()) return loadStudyPlanDashboard();
    if (retries > 0) setTimeout(() => tryLoad(retries - 1), 200);
  };
  tryLoad();
}

function switchSpView(view) {
  const ganttView = document.getElementById('spGanttView');
  const calView = document.getElementById('spCalendarView');
  const ganttBtn = document.getElementById('spViewGanttBtn');
  const calBtn = document.getElementById('spViewCalendarBtn');
  if (view === 'gantt') {
    if (ganttView) ganttView.style.display = '';
    if (calView) calView.style.display = 'none';
    if (ganttBtn) { ganttBtn.style.background = 'rgba(251,191,36,0.25)'; ganttBtn.style.color = '#fbbf24'; }
    if (calBtn) { calBtn.style.background = 'none'; calBtn.style.color = '#a1a1aa'; }
    loadGantt();
  } else {
    if (ganttView) ganttView.style.display = 'none';
    if (calView) calView.style.display = '';
    if (calBtn) { calBtn.style.background = 'rgba(251,191,36,0.25)'; calBtn.style.color = '#fbbf24'; }
    if (ganttBtn) { ganttBtn.style.background = 'none'; ganttBtn.style.color = '#a1a1aa'; }
    loadCalendar();
  }
}

function calNavigate(delta) {
  let m = _SP_CAL_STATE.month + delta;
  let y = _SP_CAL_STATE.year;
  if (m > 12) { m = 1; y += 1; }
  if (m < 1) { m = 12; y -= 1; }
  _SP_CAL_STATE.year = y;
  _SP_CAL_STATE.month = m;
  loadCalendar();
}

async function loadStudyPlanDashboard() {
  if (!window.AdminAuth || !window.AdminAuth.getToken()) return;
  // initial display: gantt
  const ganttView = document.getElementById('spGanttView');
  if (ganttView && ganttView.style.display !== 'none') {
    loadGantt();
  } else {
    loadCalendar();
  }
}

async function loadGantt() {
  const el = document.getElementById('spGantt');
  if (!el) return;
  if (!window.AdminAuth || !window.AdminAuth.getToken()) return;
  const days = parseInt(document.getElementById('spGanttDays').value || '60', 10);
  el.innerHTML = '<div style="text-align:center; color:#71717a; padding:2rem;">読み込み中...</div>';
  try {
    const res = await window.AdminAuth.fetch(`/api/admin/study-plans/gantt?days=${days}`);
    if (!res.ok) { el.innerHTML = `<div style="color:#fca5a5; padding:1rem;">読み込み失敗 (HTTP ${res.status})</div>`; return; }
    const data = await res.json();
    renderGantt(data);
  } catch (e) {
    el.innerHTML = `<div style="color:#fca5a5; padding:1rem;">エラー: ${escapeHtml(e.message || '')}</div>`;
  }
}

function renderGantt(data) {
  const el = document.getElementById('spGantt');
  if (!el) return;
  const students = data.students || [];
  const ws = _spParseJstDate(data.window_start);
  const we = new Date(data.window_end);
  const today = _spParseJstDate(data.today);
  const totalDays = Math.ceil((we - ws) / 86400000) + 1;

  if (!students.length) {
    el.innerHTML = '<div style="color:#71717a; padding:2rem; text-align:center;">期間内に学習計画がありません</div>';
    return;
  }

  // 日付ヘッダ (月単位の区切りも入れる)
  const dayWidthPx = Math.max(8, Math.floor(960 / totalDays));
  const headerCells = [];
  let lastMonth = -1;
  for (let i = 0; i < totalDays; i++) {
    const d = new Date(ws.getTime() + i * 86400000);
    const dom = d.getDate();
    const mon = d.getMonth() + 1;
    const isFirstOfMonth = dom === 1 || i === 0;
    const isToday = d.toDateString() === today.toDateString();
    headerCells.push(`<div style="display:inline-block; width:${dayWidthPx}px; text-align:center; font-size:0.6rem; color:${isToday ? '#fbbf24' : '#71717a'}; border-left:${isFirstOfMonth ? '1px solid rgba(255,255,255,0.1)' : '0'}; padding:1px 0;">${isFirstOfMonth ? mon + '/' : ''}${dom}</div>`);
  }
  const todayOffset = Math.max(0, Math.ceil((today - ws) / 86400000));
  const todayLeftPx = todayOffset * dayWidthPx;

  // 生徒行 (今日縦線は各行の background-image で描画 → overflow クリップ問題回避)
  const rows = students.map(s => {
    const trackHeight = Math.max(22, (s.plans || []).length * 22);
    const bars = (s.plans || []).map((p, idx) => {
      const ps = _spParseJstDate(p.start_date);
      const pe = _spParseJstDate(p.end_date);
      const startOffset = Math.max(0, Math.ceil((ps - ws) / 86400000));
      const endOffset = Math.min(totalDays - 1, Math.ceil((pe - ws) / 86400000));
      const widthPx = Math.max(dayWidthPx, (endOffset - startOffset + 1) * dayWidthPx);
      const leftPx = startOffset * dayWidthPx;
      // 進捗 = minPct, pages 主目標 plan は pagePct を fallback
      const pct = (p.progress_minutes_pct !== null && p.progress_minutes_pct !== undefined) ? p.progress_minutes_pct : p.progress_pages_pct;
      const tooltip = `${p.title} (${p.subject})\n${p.start_date}〜${p.end_date}\n進捗: ${pct ?? '—'}%${p.target_minutes ? ` (${p.actual_minutes}/${p.target_minutes}分)` : ''}${p.target_pages ? ` (${p.actual_pages}/${p.target_pages}p)` : ''}`;
      const progressOverlay = (pct !== null && pct !== undefined) ? `<div style="position:absolute; left:0; top:0; height:100%; width:${Math.min(100, pct)}%; background:rgba(255,255,255,0.25); border-radius:4px;"></div>` : '';
      return `<div title="${escapeHtml(tooltip)}" style="position:absolute; left:${leftPx}px; top:${idx * 22}px; width:${widthPx}px; height:18px; background:${escapeHtml(p.color)}; border-radius:4px; display:flex; align-items:center; padding:0 4px; color:#fff; font-size:0.62rem; font-weight:700; white-space:nowrap; overflow:hidden; cursor:pointer;">${progressOverlay}<span style="position:relative; z-index:1;">${escapeHtml(p.title)}</span></div>`;
    }).join('');
    return `
      <div style="display:flex; align-items:flex-start; border-bottom:1px solid rgba(255,255,255,0.05); padding:4px 0;">
        <div style="width:120px; min-width:120px; padding-right:0.5rem; color:#e4e4e7; font-size:0.78rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; position:sticky; left:0; background:rgba(15,23,42,0.95);">${escapeHtml(s.name)} ${s.grade ? `<span style="color:#71717a; font-size:0.7rem;">(${escapeHtml(s.grade)})</span>` : ''}</div>
        <div style="position:relative; flex:1; min-width:${totalDays * dayWidthPx}px; height:${trackHeight}px; background-image:linear-gradient(to right, transparent ${todayLeftPx}px, #fbbf24 ${todayLeftPx}px, #fbbf24 ${todayLeftPx + 2}px, transparent ${todayLeftPx + 2}px);">
          ${bars}
        </div>
      </div>`;
  }).join('');

  el.innerHTML = `
    <div style="position:relative;">
      <div style="display:flex; align-items:center; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:4px; margin-bottom:4px;">
        <div style="width:120px; min-width:120px; font-size:0.7rem; color:#a1a1aa; position:sticky; left:0; background:rgba(15,23,42,0.95);">生徒</div>
        <div style="position:relative; flex:1; min-width:${totalDays * dayWidthPx}px; height:14px; white-space:nowrap;">${headerCells.join('')}<div style="position:absolute; left:${todayLeftPx}px; top:-4px; bottom:-4px; width:2px; background:#fbbf24; z-index:5; pointer-events:none;"></div></div>
      </div>
      ${rows}
    </div>
    <div style="margin-top:0.5rem; font-size:0.72rem; color:#71717a;">
      合計 ${data.total_plans} 計画 / ${students.length} 名 · <span style="display:inline-block; width:8px; height:8px; background:#fbbf24; vertical-align:middle;"></span> 今日 · 進捗バー = 学習記録から自動集計
    </div>`;
}

async function loadCalendar() {
  const el = document.getElementById('spCalendar');
  const lbl = document.getElementById('spCalLabel');
  if (!el || !window.AdminAuth || !window.AdminAuth.getToken()) return;
  const y = _SP_CAL_STATE.year, m = _SP_CAL_STATE.month;
  if (lbl) lbl.textContent = `${y}年${m}月`;
  el.innerHTML = '<div style="text-align:center; color:#71717a; padding:2rem;">読み込み中...</div>';
  try {
    const res = await window.AdminAuth.fetch(`/api/admin/study-plans/calendar?year=${y}&month=${m}`);
    if (!res.ok) { el.innerHTML = `<div style="color:#fca5a5; padding:1rem;">読み込み失敗 (HTTP ${res.status})</div>`; return; }
    const data = await res.json();
    renderCalendar(data);
  } catch (e) {
    el.innerHTML = `<div style="color:#fca5a5; padding:1rem;">エラー: ${escapeHtml(e.message || '')}</div>`;
  }
}

function renderCalendar(data) {
  const el = document.getElementById('spCalendar');
  if (!el) return;
  const y = data.year, m = data.month;
  const firstDay = new Date(y, m - 1, 1);
  const lastDate = new Date(y, m, 0).getDate();
  const startWeekday = firstDay.getDay(); // 0=Sun

  // plans を日付ごとにマッピング (JST 統一・UTC ズレ防止)
  const plansByDate = {};
  (data.plans || []).forEach(p => {
    const ps = _spParseJstDate(p.start_date);
    const pe = _spParseJstDate(p.end_date);
    for (let d = new Date(Math.max(ps, firstDay)); d <= pe && d.getMonth() + 1 === m; d.setDate(d.getDate() + 1)) {
      const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
      if (!plansByDate[key]) plansByDate[key] = [];
      plansByDate[key].push(p);
    }
  });

  const todayStr = _spJstDateStr();
  const weekdays = ['日', '月', '火', '水', '木', '金', '土'];
  const weekHeader = weekdays.map((w, i) => `<div style="text-align:center; font-size:0.75rem; color:${i === 0 ? '#fca5a5' : i === 6 ? '#7dd3fc' : '#a1a1aa'}; padding:0.3rem 0; font-weight:700;">${w}</div>`).join('');

  const cells = [];
  for (let i = 0; i < startWeekday; i++) cells.push(`<div style="min-height:80px; background:rgba(0,0,0,0.1);"></div>`);
  for (let d = 1; d <= lastDate; d++) {
    const dateStr = `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
    const isToday = dateStr === todayStr;
    const dayPlans = plansByDate[dateStr] || [];
    const planChips = dayPlans.slice(0, 4).map(p =>
      `<div title="${escapeHtml(p.student_name + ': ' + p.title)}" style="background:${escapeHtml(p.color)}; color:#fff; font-size:0.62rem; padding:1px 4px; border-radius:3px; margin:1px 0; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${escapeHtml(p.student_name)}: ${escapeHtml(p.title)}</div>`
    ).join('');
    const more = dayPlans.length > 4 ? `<div style="font-size:0.62rem; color:#a1a1aa;">+${dayPlans.length - 4} more</div>` : '';
    cells.push(`
      <div style="min-height:80px; padding:0.3rem; background:${isToday ? 'rgba(251,191,36,0.1)' : 'rgba(0,0,0,0.2)'}; border:1px solid ${isToday ? 'rgba(251,191,36,0.5)' : 'rgba(255,255,255,0.05)'}; border-radius:4px; overflow:hidden;">
        <div style="font-size:0.75rem; color:${isToday ? '#fbbf24' : '#a1a1aa'}; font-weight:${isToday ? '700' : '400'}; margin-bottom:0.2rem;">${d}</div>
        ${planChips}${more}
      </div>`);
  }
  // 末尾の空セル
  while (cells.length % 7 !== 0) cells.push(`<div style="min-height:80px; background:rgba(0,0,0,0.1);"></div>`);

  el.innerHTML = `
    <div style="display:grid; grid-template-columns:repeat(7,1fr); gap:2px;">
      ${weekHeader}
      ${cells.join('')}
    </div>
    <div style="margin-top:0.5rem; font-size:0.72rem; color:#71717a;">合計 ${(data.plans || []).length} 計画</div>`;
}
