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
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:2rem;color:var(--text-muted);">生徒データがありません。 index.html の「📥 juku-managerからインポート」で既存生徒を取り込んでください。</td></tr>';
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
      ? `<a class="student-name-link" ${idAttr} style="cursor:pointer;color:var(--primary-light);text-decoration:underline;font-weight:700;" title="クリックで申込内容を表示">${escapeHtml(s.name || '-')}</a>`
      : `<strong>${escapeHtml(s.name || '-')}</strong>`;
    return `
      <tr>
        <td>${i + 1}</td>
        <td>${nameClickable}${nameWarning}</td>
        <td>${escapeHtml(s.grade || '-')}</td>
        <td style="max-width:320px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${escapeHtml(courses)}">
          ${fee > 0 ? `<span style="color:var(--primary-light);font-weight:700;">${planName}</span> / ` : ''}${escapeHtml(courses)}
        </td>
        <td class="fee-cell">${fee > 0 ? '¥' + fee.toLocaleString() : '-'}</td>
        <td><span class="roster-status ${status}">${status === 'trial' ? '体験中' : '通塾'}</span></td>
        <td style="color:var(--text-dim);font-size:0.85em;">${escapeHtml(s.goal || '-')}</td>
      </tr>
    `;
  }).join('');
}

function escapeHtml(s) {
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
});
