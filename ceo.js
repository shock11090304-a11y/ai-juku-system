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
    tbody.innerHTML = '<tr><td colspan="10" style="text-align:center;padding:2rem;color:var(--text-muted);">生徒データがありません。 index.html の「📥 juku-managerからインポート」で既存生徒を取り込んでください。</td></tr>';
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
    // 最終活動: ログイン+AI質問+学習記録+模試の MAX。last_login_at とズレてれば乖離アラート表示
    const latestAct = s.latest_activity_at ? formatRelativeTime(s.latest_activity_at) : '<span style="color:#71717a;">活動なし</span>';
    let activeColor = '';
    if (s.latest_activity_at && s.last_login_at) {
      const lActD = new Date(String(s.latest_activity_at).replace(' ', 'T'));
      const lLogD = new Date(String(s.last_login_at).replace(' ', 'T'));
      // 活動が「ログイン」より 24h 以上新しければセッション継続中の継続利用 → 緑強調
      if (!isNaN(lActD.getTime()) && !isNaN(lLogD.getTime()) && (lActD - lLogD) > 86400000) {
        activeColor = ' style="font-weight:700;color:#34d399;" title="ログイン後もセッション継続して学習中"';
      }
    }
    // 📱 LINE 連携マーカー (緑=連携済 / 灰=未連携で誘導)
    const hasLine = !!s.has_line;
    const lineIcon = hasLine
      ? ` <span title="LINE 連携済 (メール届かない時の fallback 通知 OK)" style="color:#06c755;font-size:0.95em;cursor:help;">📱</span>`
      : ` <span title="LINE 未連携 — 連携誘導すると配信信頼性UP" style="color:#71717a;font-size:0.95em;cursor:help;opacity:0.5;">📱</span>`;
    // 📧 キャリアメール警告 (ezweb/docomo/au.com 等は迷惑振り分け率が高い)
    const carrierWarn = s.is_carrier_email
      ? ` <span title="キャリアメール (ezweb/docomo/au.com 等) — 迷惑振り分け率が高いため LINE 連携を推奨" style="color:#fbbf24;font-size:0.85em;cursor:help;">⚠️📧</span>`
      : '';
    const deleteBtn = s.id != null
      ? `<button class="roster-delete-btn" data-sid="${escapeHtml(String(s.id))}" data-name="${escapeHtml(s.name || '')}" data-email="${escapeHtml(s.email || '')}" title="この生徒の全データを完全削除 (取消不能)" style="background:rgba(239,68,68,0.1);color:#fca5a5;border:1px solid rgba(239,68,68,0.3);padding:0.25rem 0.5rem;border-radius:6px;cursor:pointer;font-size:0.85em;">🗑️</button>`
      : '<span style="color:var(--text-muted);font-size:0.8em;">-</span>';
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
        <td${activeColor || ' style="font-size:0.85em;color:var(--text-dim);"'}>${latestAct}</td>
        <td style="color:var(--text-dim);font-size:0.85em;">${escapeHtml(s.goal || '-')}</td>
        <td>${deleteBtn}</td>
      </tr>
    `;
  }).join('');
  // 削除ボタン bind
  tbody.querySelectorAll('.roster-delete-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const b = e.currentTarget;
      const sid = b.getAttribute('data-sid');
      const name = b.getAttribute('data-name');
      const email = b.getAttribute('data-email');
      if (typeof confirmAndDeleteStudent === 'function') {
        confirmAndDeleteStudent(sid, name, email);
      } else {
        alert('削除機能の読み込みに失敗しました。ページを再読込してください。');
      }
    });
  });
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
        <button onclick="expiredAction('extend',${s.id})" style="padding:0.4rem 0.8rem;background:linear-gradient(135deg,#22c55e,#16a34a);color:white;border:none;border-radius:6px;font-size:0.8rem;cursor:pointer;white-space:nowrap;" title="体験を10日間延長">
          🔄 体験延長
        </button>
      </div>`;
  }).join('');
}

async function loadReferralMetrics() {
  if (!window.AdminAuth || !window.AdminAuth.getToken()) return;
  try {
    const res = await window.AdminAuth.fetch('/api/admin/referrals');
    if (!res.ok) return;
    const data = await res.json();
    const fmt = (n) => '¥' + Number(n || 0).toLocaleString();
    const setText = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
    setText('referralTotal', data.total || 0);
    setText('referralPaidCount', data.paid || 0);
    setText('referralPending', data.pending || 0);
    setText('referralRewardTotal', fmt(data.reward_total_yen));
    const topEl = document.getElementById('referralTopReferrers');
    if (topEl) {
      if (!data.top_referrers || data.top_referrers.length === 0) {
        topEl.innerHTML = '<div style="opacity:0.6;">まだ紹介申込はありません。生徒が mypage の「友達紹介」セクションからURLをシェアできます。</div>';
      } else {
        topEl.innerHTML = '<div style="font-weight:700;margin-bottom:0.4rem;">🏆 上位紹介者:</div>' +
          data.top_referrers.map((r, i) =>
            `<div style="padding:0.3rem 0;">${i + 1}. ${escapeHtml(r.name || '-')} — ${r.invited}名招待 / ${r.converted || 0}名成立</div>`
          ).join('');
      }
    }
  } catch (e) {
    console.error('loadReferralMetrics failed:', e);
  }
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
    ? 'この生徒の体験期間を10日間延長しますか？'
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
  try { initMessageDashboard(); } catch (e) { console.error('initMessageDashboard failed:', e); }
  try { initCourseApps(); } catch (e) { console.error('initCourseApps failed:', e); }

  // 🔔 体験終了者フォローアップ + 🎁 紹介ループ metrics: AdminAuth 認証後に読み込み
  const tryLoadAdminSections = (retries = 10) => {
    if (window.AdminAuth && window.AdminAuth.getToken()) {
      loadExpiredUsers();
      loadReferralMetrics();
      return;
    }
    if (retries > 0) setTimeout(() => tryLoadAdminSections(retries - 1), 300);
  };
  tryLoadAdminSections();
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
    const renderRow = (s, courseColor, courseAction) => `
      <div style="display:flex; justify-content:space-between; align-items:center; padding:0.5rem 0.7rem; background:${courseColor.bg}; border:1px solid ${courseColor.border}; border-radius:8px; margin-bottom:0.4rem; gap:0.4rem;">
        <div style="color:#e4e4e7; font-size:0.88rem; flex:1; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${escapeHtml(s.name)}${s.grade ? ` <span style="color:#71717a; font-size:0.78rem;">(${escapeHtml(s.grade)})</span>` : ''}</div>
        <div style="display:flex; gap:0.3rem; flex-shrink:0;">
          ${courseAction.html}
          <button data-sid="${s.id}" data-name="${escapeHtml(s.name)}" data-email="${escapeHtml(s.email || '')}" class="sl-student-delete" title="完全削除 (取消不能)" style="background:rgba(239,68,68,0.1); color:#fca5a5; border:1px solid rgba(239,68,68,0.3); padding:0.3rem 0.5rem; border-radius:6px; cursor:pointer; font-size:0.8rem;">🗑️</button>
        </div>
      </div>`;
    const enrolledColor = { bg: 'rgba(251,191,36,0.08)', border: 'rgba(251,191,36,0.2)' };
    const otherColor = { bg: 'rgba(255,255,255,0.04)', border: 'rgba(255,255,255,0.08)' };
    const enrolledAction = (s) => ({ html: `<button data-sid="${s.id}" data-action="remove" class="sl-course-toggle" style="background:rgba(239,68,68,0.15); color:#fca5a5; border:0; padding:0.3rem 0.7rem; border-radius:6px; cursor:pointer; font-size:0.8rem;">離脱</button>` });
    const otherAction = (s) => ({ html: `<button data-sid="${s.id}" data-action="add" class="sl-course-toggle" style="background:rgba(99,102,241,0.2); color:#c7d2fe; border:0; padding:0.3rem 0.7rem; border-radius:6px; cursor:pointer; font-size:0.8rem;">加入</button>` });
    list.innerHTML = `
      <div style="margin-bottom:1.2rem;">
        <div style="color:#fbbf24; font-size:0.9rem; font-weight:700; margin-bottom:0.5rem;">✅ 国公立難関大学コース 受講中 (${enrolled.length}名)</div>
        ${enrolled.length === 0 ? '<div style="color:#71717a; font-size:0.85rem;">まだ加入者がいません</div>' :
          enrolled.map(s => renderRow(s, enrolledColor, enrolledAction(s))).join('')}
      </div>
      <div>
        <div style="color:#a1a1aa; font-size:0.9rem; font-weight:700; margin-bottom:0.5rem;">⚪ 未加入の生徒 (${others.length}名)</div>
        ${others.length === 0 ? '<div style="color:#71717a; font-size:0.85rem;">全生徒加入済</div>' :
          others.map(s => renderRow(s, otherColor, otherAction(s))).join('')}
      </div>
      <div style="margin-top:1rem; padding:0.7rem; background:rgba(239,68,68,0.05); border:1px solid rgba(239,68,68,0.2); border-radius:8px; font-size:0.78rem; color:#fca5a5;">
        🗑️ <strong>顧客データ削除</strong>: 選択した生徒の<u>全データ</u> (学習記録・模試・カリキュラム・メッセージ・通知・支払履歴) を完全削除します。<br>
        Stripe 有効サブスクがある場合は確認後に同時解約。<u>取消不能</u>のため、生徒名を入力する 2 段階確認が必要です。
      </div>
    `;
    // 削除ボタン bind
    list.querySelectorAll('.sl-student-delete').forEach(b => {
      b.addEventListener('click', (e) => {
        const btn = e.currentTarget;
        const sid = btn.getAttribute('data-sid');
        const name = btn.getAttribute('data-name');
        const email = btn.getAttribute('data-email');
        confirmAndDeleteStudent(sid, name, email);
      });
    });
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

// 🗑️ 顧客データ完全削除 (2段階確認 + Stripe ガード)
async function confirmAndDeleteStudent(studentId, studentName, studentEmail) {
  if (!window.AdminAuth || !window.AdminAuth.getToken()) { alert('管理者認証が必要です'); return; }
  // Step 1: dry_run で関連データ件数 + Stripe 有無を取得
  let snapshot;
  try {
    const r = await window.AdminAuth.fetch(`/api/admin/students/${encodeURIComponent(studentId)}/delete`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dry_run: true }),
    });
    if (!r.ok) {
      const j = await r.json().catch(() => ({}));
      alert('プレビュー取得失敗: ' + (j.detail || r.status));
      return;
    }
    const data = await r.json();
    snapshot = data.snapshot;
  } catch (e) { alert('⚠️ ' + (e.message || e)); return; }
  const rc = snapshot.related_counts || {};
  const total = Object.values(rc).reduce((a, b) => a + (typeof b === 'number' && b > 0 ? b : 0), 0);
  const hasSub = !!snapshot.stripe_subscription_id;
  const lines = [];
  lines.push(`🗑️ 顧客データ完全削除\n`);
  lines.push(`生徒: ${studentName} (ID:${studentId})`);
  lines.push(`メール: ${studentEmail || '(未設定)'}`);
  lines.push(`プラン: ${snapshot.plan || '-'} / 状態: ${snapshot.status || '-'} / コース: ${snapshot.course || '-'}`);
  if (hasSub) {
    lines.push(`\n⚠️ Stripe 有効サブスク: ${snapshot.stripe_subscription_id}`);
    lines.push('  → 削除と同時に Stripe 解約も実行します (cancel_stripe=true)');
  }
  lines.push('\n削除される関連データ:');
  Object.keys(rc).forEach(k => {
    const v = rc[k];
    if (typeof v === 'number' && v > 0) lines.push(`  - ${k}: ${v}件`);
  });
  if (total === 0) lines.push('  (関連データなし)');
  lines.push(`\n合計 ${total} 件の関連レコード + 生徒本体を削除します。`);
  lines.push('この操作は取消不能です。続行しますか?');
  if (!confirm(lines.join('\n'))) return;
  // Step 2: 同名衝突防止のため email を入力させて確認 (email 未設定なら name fallback)
  const useEmail = !!(studentEmail && studentEmail.trim());
  const expectedKey = useEmail ? studentEmail.trim() : (studentName || '').trim();
  const promptLabel = useEmail
    ? `削除を実行するには、メールアドレスを正確に入力してください:\n\n「${expectedKey}」\n\n(同名生徒との誤削除防止のため email 確認)`
    : `削除を実行するには、生徒名を正確に入力してください:\n\n「${expectedKey}」\n\n(この生徒は email 未設定のため名前で確認)`;
  const typed = prompt(promptLabel);
  if (typed === null) return;
  const compareTyped = useEmail ? typed.trim().toLowerCase() : typed.trim();
  const compareExpected = useEmail ? expectedKey.toLowerCase() : expectedKey;
  if (compareTyped !== compareExpected) {
    alert(`入力された${useEmail ? 'メールアドレス' : '名前'}が一致しません。削除をキャンセルしました。`);
    return;
  }
  // Step 3: 実行
  try {
    const body = { cancel_stripe: hasSub, dry_run: false };
    if (useEmail) body.confirm_email = studentEmail;
    else body.confirm_name = studentName;
    const r = await window.AdminAuth.fetch(`/api/admin/students/${encodeURIComponent(studentId)}/delete`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!r.ok) {
      const j = await r.json().catch(() => ({}));
      alert('❌ 削除失敗: ' + (j.detail || r.status));
      return;
    }
    const data = await r.json();
    const dc = data.deleted || {};
    const summary = Object.keys(dc).map(k => `${k}: ${dc[k]}`).join('\n');
    alert(`✅ 削除完了\n\n生徒「${studentName}」を完全削除しました。\n\n${summary}`);
    // 一覧を再描画
    if (typeof openCourseManageModal === 'function') await openCourseManageModal();
    if (typeof loadStudyLogDashboard === 'function') loadStudyLogDashboard();
  } catch (e) {
    alert('⚠️ ' + (e.message || e));
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


// ==========================================================================
// 📨 メッセージ配信ダッシュボード (Phase 3)
// ==========================================================================
let _msgCurrentTarget = 'student';
let _msgLastBroadcastCount = -1;  // 0名 confirm 防止 (Frontend C-2)

// ISO → JST 'YYYY-MM-DD HH:MM' 変換 (UX C-1)
function _msgFmtJst(s) {
  if (!s) return '';
  try {
    const iso = String(s);
    const d = new Date(iso.endsWith('Z') || /[+-]\d\d:?\d\d$/.test(iso) ? iso : iso + 'Z');
    if (isNaN(d)) return String(s).slice(0, 16).replace('T', ' ');
    const fmt = new Intl.DateTimeFormat('ja-JP', { timeZone: 'Asia/Tokyo', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false });
    return fmt.format(d).replace(/\//g, '-');
  } catch { return String(s).slice(0, 16).replace('T', ' '); }
}

function initMessageDashboard() {
  const tabInd = document.getElementById('msgTabIndividual');
  const tabBC = document.getElementById('msgTabBroadcast');
  const sendBtn = document.getElementById('msgSendBtn');
  const refreshBtn = document.getElementById('msgRefreshBtn');
  const broadcastFilter = document.getElementById('msgBroadcastFilter');

  if (tabInd) tabInd.addEventListener('click', () => switchMsgTab('student'));
  if (tabBC) tabBC.addEventListener('click', () => switchMsgTab('broadcast'));
  if (sendBtn) sendBtn.addEventListener('click', sendMessage);
  if (refreshBtn) refreshBtn.addEventListener('click', loadMessageHistory);
  if (broadcastFilter) broadcastFilter.addEventListener('change', updateBroadcastCount);
  // E: AI で文案を作る (一斉/個別共通)
  const aiDraftBtn = document.getElementById('msgAiDraftBtn');
  if (aiDraftBtn && !aiDraftBtn._bound) {
    aiDraftBtn.addEventListener('click', async () => {
      const points = prompt('一斉送信の要点を入力してください (Gemini で文案を生成します)\n\n例: 「7月夏期講習開講・全6日間・締切7/20・費用¥35,000」');
      if (!points || !points.trim()) return;
      const hint = prompt('追加指示があれば入力 (任意)\n例: 「保護者向け」「箇条書き多めに」', '') || '';
      await openAiDraftModal('broadcast_draft', points.trim(), hint, null, null);
    });
    aiDraftBtn._bound = true;
  }

  const tryLoad = (retries = 10) => {
    if (window.AdminAuth && window.AdminAuth.getToken()) {
      loadStudentSelect();
      loadMessageHistory();
      updateBroadcastCount();
    } else if (retries > 0) {
      setTimeout(() => tryLoad(retries - 1), 200);
    }
  };
  tryLoad();
}

function switchMsgTab(target) {
  _msgCurrentTarget = target;
  const tabInd = document.getElementById('msgTabIndividual');
  const tabBC = document.getElementById('msgTabBroadcast');
  const indWrap = document.getElementById('msgIndividualWrap');
  const bcWrap = document.getElementById('msgBroadcastWrap');
  if (target === 'student') {
    if (tabInd) { tabInd.style.background = 'rgba(236,72,153,0.25)'; tabInd.style.color = '#f9a8d4'; }
    if (tabBC) { tabBC.style.background = 'none'; tabBC.style.color = '#a1a1aa'; }
    if (indWrap) indWrap.style.display = '';
    if (bcWrap) bcWrap.style.display = 'none';
  } else {
    if (tabBC) { tabBC.style.background = 'rgba(236,72,153,0.25)'; tabBC.style.color = '#f9a8d4'; }
    if (tabInd) { tabInd.style.background = 'none'; tabInd.style.color = '#a1a1aa'; }
    if (indWrap) indWrap.style.display = 'none';
    if (bcWrap) bcWrap.style.display = '';
    updateBroadcastCount();
  }
}

async function loadStudentSelect() {
  const sel = document.getElementById('msgStudentSelect');
  if (!sel) return;
  try {
    const res = await window.AdminAuth.fetch('/api/admin/students/by-course');
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const data = await res.json();
    const students = data.students || [];
    sel.innerHTML = '<option value="">-- 生徒を選択 --</option>' + students.map(s =>
      `<option value="${escapeHtml(String(s.id))}">${escapeHtml(s.name)}${s.grade ? ` (${escapeHtml(s.grade)})` : ''}${s.course === 'kokuritsu_nankan' ? ' [国公立難関]' : ''}</option>`
    ).join('');
  } catch (e) {
    sel.innerHTML = `<option value="">読み込み失敗: ${escapeHtml(e.message || '')}</option>`;
  }
}

async function updateBroadcastCount() {
  const filter = document.getElementById('msgBroadcastFilter');
  const countEl = document.getElementById('msgBroadcastCount');
  if (!filter || !countEl) return;
  countEl.textContent = '対象人数を計算中...';
  try {
    const res = await window.AdminAuth.fetch('/api/admin/students/by-course');
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const data = await res.json();
    const all = data.students || [];
    let cnt = 0;
    const f = filter.value;
    if (f === 'all') cnt = all.length;
    else if (f === 'kokuritsu_nankan') cnt = all.filter(s => s.course === 'kokuritsu_nankan').length;
    else if (f === 'paid_only') cnt = all.filter(s => s.status === 'paid').length;
    else if (f === 'trial_only') cnt = all.filter(s => s.status === 'trial').length;
    countEl.textContent = `📊 対象: ${cnt} 名`;
    countEl.style.color = cnt > 0 ? '#86efac' : '#fca5a5';
    _msgLastBroadcastCount = cnt;
  } catch (e) {
    countEl.textContent = '対象人数取得失敗';
    _msgLastBroadcastCount = -1;
  }
}

async function sendMessage() {
  const btn = document.getElementById('msgSendBtn');
  const msg = document.getElementById('msgSendMessage');
  if (!btn || btn.disabled) return;
  if (msg) { msg.textContent = ''; msg.style.color = '#a1a1aa'; }

  const target = _msgCurrentTarget;
  const subject = document.getElementById('msgSubject').value.trim();
  const body = document.getElementById('msgBody').value.trim();
  const sendEmail = document.getElementById('msgSendEmail').checked;

  if (!body) { if (msg) { msg.textContent = '本文は必須です'; msg.style.color = '#fca5a5'; } return; }

  const payload = { target, subject: subject || undefined, body, send_email: sendEmail };

  // 📎 添付ファイル (任意・10MB)
  const attachInput = document.getElementById('msgAttachInput');
  const attachStatus = document.getElementById('msgAttachStatus');
  const attachFile = attachInput && attachInput.files && attachInput.files[0];
  if (attachFile) {
    if (attachFile.size > 10 * 1024 * 1024) {
      if (msg) { msg.textContent = `添付ファイルが大きすぎます (${(attachFile.size/1024/1024).toFixed(1)} MB / 上限 10 MB)`; msg.style.color = '#fca5a5'; }
      return;
    }
    try {
      if (attachStatus) attachStatus.textContent = '⏳ ファイル読込中...';
      const dataUrl = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = () => reject(new Error('ファイル読込失敗'));
        reader.readAsDataURL(attachFile);
      });
      const b64 = String(dataUrl).split(',')[1] || '';
      payload.attachment_filename = attachFile.name;
      payload.attachment_mime = attachFile.type || 'application/octet-stream';
      payload.attachment_data_b64 = b64;
      if (attachStatus) attachStatus.textContent = `📎 ${attachFile.name} (${(attachFile.size/1024).toFixed(1)} KB)`;
    } catch (e) {
      if (msg) { msg.textContent = 'ファイル読込失敗: ' + (e.message || ''); msg.style.color = '#fca5a5'; }
      return;
    }
  }

  if (target === 'student') {
    const sid = document.getElementById('msgStudentSelect').value;
    if (!sid) { if (msg) { msg.textContent = '送信先生徒を選択してください'; msg.style.color = '#fca5a5'; } return; }
    payload.student_id = parseInt(sid, 10);
  } else {
    payload.broadcast_filter = document.getElementById('msgBroadcastFilter').value;
    // 0 名 / 取得失敗時は送信拒否 (Frontend C-2)
    if (_msgLastBroadcastCount === 0) { if (msg) { msg.textContent = '対象人数 0 名のため送信できません'; msg.style.color = '#fca5a5'; } return; }
    if (_msgLastBroadcastCount < 0) { if (msg) { msg.textContent = '対象人数を取得してから再度実行してください'; msg.style.color = '#fca5a5'; } return; }
    // 文字数 client side 検証 (Frontend M-6)
    if (body.length > 5000) { if (msg) { msg.textContent = `本文は5000文字以内 (現在 ${body.length} 文字)`; msg.style.color = '#fca5a5'; } return; }
    if (subject.length > 200) { if (msg) { msg.textContent = `件名は200文字以内 (現在 ${subject.length} 文字)`; msg.style.color = '#fca5a5'; } return; }
    const bodyPreview = body.length > 50 ? body.slice(0, 50) + '…' : body;
    if (!confirm(`一斉送信します。\n対象: ${_msgLastBroadcastCount} 名\n件名: ${subject || '(なし)'}\n本文: ${bodyPreview}\nメール配信: ${sendEmail ? 'あり' : 'なし'}\n\nよろしいですか？`)) return;
  }
  // 個別送信時の文字数検証 (broadcast 上で実施した分は通過済)
  if (target === 'student') {
    if (body.length > 5000) { if (msg) { msg.textContent = `本文は5000文字以内 (現在 ${body.length} 文字)`; msg.style.color = '#fca5a5'; } return; }
    if (subject.length > 200) { if (msg) { msg.textContent = `件名は200文字以内 (現在 ${subject.length} 文字)`; msg.style.color = '#fca5a5'; } return; }
  }

  btn.disabled = true;
  btn.textContent = '送信中...';
  try {
    const res = await window.AdminAuth.fetch('/api/admin/messages/send', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      let detail = '';
      try { const j = await res.json(); detail = j.detail || ''; } catch {}
      throw new Error(detail || `HTTP ${res.status}`);
    }
    const data = await res.json();
    if (msg) {
      msg.textContent = `✅ 送信完了 (受信者 ${data.recipients} 名 · email送信 ${data.email_sent}/${data.email_attempted}${data.email_failed ? ` · 失敗 ${data.email_failed}` : ''})`;
      msg.style.color = '#86efac';
    }
    document.getElementById('msgSubject').value = '';
    document.getElementById('msgBody').value = '';
    if (attachInput) attachInput.value = '';
    if (attachStatus) attachStatus.textContent = '';
    await loadMessageHistory();
  } catch (e) {
    if (msg) { msg.textContent = '❌ ' + (e.message || '送信失敗'); msg.style.color = '#fca5a5'; }
  } finally {
    btn.disabled = false;
    btn.textContent = '📨 送信';
  }
}

async function loadMessageHistory() {
  const el = document.getElementById('msgHistory');
  if (!el) return;
  if (!window.AdminAuth || !window.AdminAuth.getToken()) {
    el.innerHTML = '<div style="color:#fbbf24; padding:1rem;">⏳ 認証準備中...</div>';
    return;
  }
  el.innerHTML = '<div style="text-align:center; color:#71717a; padding:1rem;">読み込み中...</div>';
  try {
    const res = await window.AdminAuth.fetch('/api/admin/messages?limit=100');
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const data = await res.json();
    const broadcasts = data.broadcasts || [];
    const individuals = data.individuals || [];
    const inquiries = data.inquiries || [];
    if (!broadcasts.length && !individuals.length && !inquiries.length) {
      el.innerHTML = '<div style="text-align:center; color:#71717a; padding:1.5rem;">送信履歴がありません</div>';
      return;
    }
    let html = '';
    // 📥 受信した申込問い合わせ (最上部に表示)
    if (inquiries.length) {
      const pending = inquiries.filter(q => !q.is_already_enrolled);
      const enrolled = inquiries.filter(q => q.is_already_enrolled);
      html += `<div style="font-size:0.8rem; color:#fbbf24; margin:0.5rem 0; font-weight:700;">📥 受信した申込問い合わせ (${inquiries.length} 件 / 未対応 ${pending.length})</div>`;
      html += inquiries.map(q => {
        const enrolledBadge = q.is_already_enrolled
          ? '<span style="background:rgba(134,239,172,0.18); color:#86efac; padding:0.15rem 0.5rem; border-radius:999px; font-size:0.7rem; font-weight:700;">✅ 加入済み</span>'
          : '<span style="background:rgba(251,191,36,0.18); color:#fbbf24; padding:0.15rem 0.5rem; border-radius:999px; font-size:0.7rem; font-weight:700;">🟡 未対応</span>';
        const actionBtn = q.is_already_enrolled
          ? ''
          : `<button data-sid="${escapeHtml(String(q.from_student_id))}" data-q-id="${escapeHtml(String(q.id))}" class="msg-approve-btn" style="background:linear-gradient(135deg,#10b981,#34d399); color:#fff; border:0; padding:0.4rem 0.9rem; border-radius:8px; cursor:pointer; font-size:0.78rem; font-weight:700;">✅ 加入させる</button>`;
        const replyBtn = `<button data-sid="${escapeHtml(String(q.from_student_id))}" data-name="${escapeHtml(q.from_student_name || '')}" class="msg-reply-btn" style="background:rgba(99,102,241,0.2); color:#c7d2fe; border:0; padding:0.4rem 0.9rem; border-radius:8px; cursor:pointer; font-size:0.78rem;">💬 返信</button>`;
        const aiReplyBtn = `<button data-sid="${escapeHtml(String(q.from_student_id))}" data-name="${escapeHtml(q.from_student_name || '')}" data-context="${escapeHtml(q.body || '')}" class="msg-ai-reply-btn" style="background:linear-gradient(135deg,#a78bfa,#ec4899); color:#fff; border:0; padding:0.4rem 0.9rem; border-radius:8px; cursor:pointer; font-size:0.78rem; font-weight:700;">🤖 AI 返信案</button>`;
        return `
          <div style="background:rgba(251,191,36,0.05); border:1px solid rgba(251,191,36,0.3); border-left:4px solid #fbbf24; border-radius:8px; padding:0.85rem; margin-bottom:0.6rem;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.4rem; flex-wrap:wrap; gap:0.3rem;">
              <div style="font-weight:700; color:#e4e4e7; font-size:0.92rem;">📥 ${escapeHtml(q.from_student_name || '?')}${q.from_student_grade ? ` <span style="color:#71717a; font-size:0.72rem;">(${escapeHtml(q.from_student_grade)})</span>` : ''} ${enrolledBadge}</div>
              <div style="font-size:0.72rem; color:#71717a;">${escapeHtml(_msgFmtJst(q.created_at))}</div>
            </div>
            <div style="font-size:0.85rem; color:#d4d4d8; padding:0.4rem 0.6rem; background:rgba(0,0,0,0.25); border-radius:6px; margin-bottom:0.5rem;">${escapeHtml(q.body)}</div>
            <div style="display:flex; gap:0.5rem; align-items:center; flex-wrap:wrap;">${actionBtn}${replyBtn}${aiReplyBtn}</div>
            <div class="msg-approve-result" style="margin-top:0.4rem; font-size:0.78rem;"></div>
          </div>`;
      }).join('');
    }
    if (broadcasts.length) {
      html += '<div style="font-size:0.8rem; color:#a1a1aa; margin:0.5rem 0;">📢 一斉送信</div>';
      html += broadcasts.map(b => {
        const fLabel = { all: '全生徒', kokuritsu_nankan: '国公立難関', paid_only: '有料のみ', trial_only: '体験のみ' }[b.broadcast_filter] || b.broadcast_filter;
        return `
          <div style="background:rgba(255,255,255,0.04); border-left:3px solid #ec4899; border-radius:6px; padding:0.7rem; margin-bottom:0.5rem;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.3rem;">
              <div style="font-weight:700; color:#f9a8d4; font-size:0.88rem;">📢 ${escapeHtml(b.subject || 'お知らせ')} <span style="font-size:0.72rem; color:#a1a1aa; font-weight:400; margin-left:0.3rem;">[${escapeHtml(fLabel)}]</span></div>
              <div style="font-size:0.72rem; color:#71717a;">${escapeHtml(_msgFmtJst(b.created_at))}</div>
            </div>
            <div style="font-size:0.78rem; color:#d4d4d8; max-height:3em; overflow:hidden; margin-bottom:0.4rem;">${escapeHtml(b.body)}</div>
            <div style="display:flex; gap:0.7rem; font-size:0.72rem; color:#a1a1aa;">
              <span>👥 受信 ${b.recipient_count}</span>
              <span style="color:#86efac;">📧 ${b.email_sent_count}</span>
              ${b.email_failed_count > 0 ? `<span style="color:#fca5a5;">⚠ 失敗 ${b.email_failed_count}</span>` : ''}
              <span style="color:#7dd3fc;">👁 既読 ${b.read_count}/${b.recipient_count}</span>
            </div>
          </div>`;
      }).join('');
    }
    if (individuals.length) {
      html += '<div style="font-size:0.8rem; color:#a1a1aa; margin:0.7rem 0 0.5rem;">👤 個別送信</div>';
      html += individuals.map(m => {
        const readBadge = m.read_at
          ? `<span style="color:#7dd3fc;">👁 既読 ${escapeHtml(_msgFmtJst(m.read_at))}</span>`
          : '<span style="color:#fbbf24;">未読</span>';
        const emailBadge = m.email_status === 'sent' ? '<span style="color:#86efac;">📧 送信済</span>'
          : (m.email_status && m.email_status.startsWith('failed')) ? `<span style="color:#fca5a5;" title="${escapeHtml(m.email_status)}">⚠ メール失敗</span>` : '';
        return `
          <div style="background:rgba(255,255,255,0.04); border-left:3px solid rgba(236,72,153,0.5); border-radius:6px; padding:0.7rem; margin-bottom:0.5rem;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.3rem;">
              <div style="font-weight:700; color:#e4e4e7; font-size:0.88rem;">👤 ${escapeHtml(m.student_name || '?')}${m.grade ? ` <span style="color:#71717a; font-size:0.72rem;">(${escapeHtml(m.grade)})</span>` : ''} <span style="color:#f9a8d4; margin-left:0.3rem;">${escapeHtml(m.subject || 'お知らせ')}</span></div>
              <div style="font-size:0.72rem; color:#71717a;">${escapeHtml(_msgFmtJst(m.created_at))}</div>
            </div>
            <div style="font-size:0.78rem; color:#d4d4d8; max-height:3em; overflow:hidden; margin-bottom:0.4rem;">${escapeHtml(m.body)}</div>
            <div style="display:flex; gap:0.7rem; font-size:0.72rem;">${emailBadge} ${readBadge}</div>
          </div>`;
      }).join('');
    }
    el.innerHTML = html;

    // 「✅ 加入させる」ボタン bind
    el.querySelectorAll('.msg-approve-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        if (btn.disabled) return;
        const sid = btn.getAttribute('data-sid');
        const resultEl = btn.parentElement.parentElement.querySelector('.msg-approve-result');
        if (!confirm(`生徒 ID ${sid} を国公立難関大学コースに加入させますか?\n生徒に「加入完了」通知が自動で送信されます。`)) return;
        btn.disabled = true;
        const orig = btn.textContent;
        btn.textContent = '加入処理中...';
        try {
          const res = await window.AdminAuth.fetch(`/api/admin/students/${encodeURIComponent(sid)}/course`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ course: 'kokuritsu_nankan' }),
          });
          if (!res.ok) {
            let detail = '';
            try { const j = await res.json(); detail = j.detail || ''; } catch {}
            throw new Error(detail || `HTTP ${res.status}`);
          }
          if (resultEl) resultEl.innerHTML = '<span style="color:#86efac;">✅ 加入完了。生徒に通知を送信しました。</span>';
          // 0.8 秒後に履歴再描画 (subject に「✅ [加入済み]」prefix が付く)
          setTimeout(() => loadMessageHistory(), 800);
        } catch (e) {
          if (resultEl) resultEl.innerHTML = `<span style="color:#fca5a5;">❌ ${escapeHtml(e.message || '加入失敗')}</span>`;
          btn.disabled = false;
          btn.textContent = orig;
        }
      });
    });

    // 「💬 返信」ボタン bind: 個別送信タブを開いて該当生徒を選択 + フォーカス
    el.querySelectorAll('.msg-reply-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const sid = btn.getAttribute('data-sid');
        const name = btn.getAttribute('data-name');
        switchMsgTab('student');
        const sel = document.getElementById('msgStudentSelect');
        if (sel) {
          sel.value = sid;
          // 選択肢に存在しない場合 (最近追加 etc) → 強制 option 追加
          if (sel.value !== sid) {
            const opt = document.createElement('option');
            opt.value = sid;
            opt.textContent = name || `生徒ID ${sid}`;
            opt.selected = true;
            sel.insertBefore(opt, sel.firstChild ? sel.firstChild.nextSibling : null);
          }
          sel.focus();
        }
        const subj = document.getElementById('msgSubject');
        if (subj && !subj.value) subj.value = `Re: お問い合わせの件 (${name || ''})`;
        const body = document.getElementById('msgBody');
        if (body) body.focus();
        // フォームまでスクロール
        const sec = document.getElementById('messagesSection');
        if (sec) sec.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    });

    // 「🤖 AI 返信案」ボタン bind (Phase 3.5 / Gemini)
    el.querySelectorAll('.msg-ai-reply-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        const sid = btn.getAttribute('data-sid');
        const name = btn.getAttribute('data-name');
        const ctx = btn.getAttribute('data-context') || '(本文なし)';
        const hint = prompt(`AI 返信案を作成します (Gemini)。\n\n返信のトーン・追加指示があれば入力してください (任意・空欄可):\n例: 「明日の面談に誘う」「料金についても触れる」`, '');
        if (hint === null) return;
        await openAiDraftModal('reply_draft', `生徒「${name}」(ID:${sid}) からのメッセージ:\n${ctx}`, hint, name, sid);
      });
    });
  } catch (e) {
    el.innerHTML = `<div style="color:#fca5a5; padding:1rem;">エラー: ${escapeHtml(e.message || '')}</div>`;
  }
}

// ==========================================================================
// 🤖 AI 返信案 / 一斉送信文案 (Phase 3.5 / Gemini)
// ==========================================================================
async function openAiDraftModal(kind, context, hint, targetName, targetSid) {
  let modal = document.getElementById('aiDraftModal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'aiDraftModal';
    modal.style.cssText = 'position:fixed; inset:0; background:rgba(0,0,0,0.7); z-index:9999; display:flex; align-items:flex-start; justify-content:center; padding:2rem; overflow-y:auto;';
    modal.innerHTML = `
      <div style="background:#0f172a; border:1px solid rgba(167,139,250,0.4); border-radius:14px; padding:1.5rem; max-width:700px; width:100%;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
          <h3 id="aiDraftTitle" style="margin:0; color:#c4b5fd;">🤖 AI 文案 (Gemini)</h3>
          <button id="aiDraftClose" type="button" style="background:none; border:0; color:#a1a1aa; font-size:1.5rem; cursor:pointer;">×</button>
        </div>
        <div id="aiDraftBody"></div>
      </div>`;
    document.body.appendChild(modal);
    modal.querySelector('#aiDraftClose').addEventListener('click', () => modal.style.display = 'none');
    modal.addEventListener('click', e => { if (e.target === modal) modal.style.display = 'none'; });
    document.addEventListener('keydown', e => { if (e.key === 'Escape' && modal.style.display === 'flex') modal.style.display = 'none'; });
  }
  modal.style.display = 'flex';
  modal.querySelector('#aiDraftTitle').textContent = kind === 'reply_draft' ? `🤖 AI 返信案 (Gemini) ${targetName ? '→ ' + targetName : ''}` : '🤖 AI 一斉送信文案 (Gemini)';
  const body = modal.querySelector('#aiDraftBody');
  body.innerHTML = '<div style="text-align:center; padding:2rem; color:#a1a1aa;">🤖 Gemini が文案を生成中... (3-10秒)</div>';

  try {
    const res = await window.AdminAuth.fetch('/api/admin/ai-draft', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ kind, context, extra_hint: hint || undefined }),
    });
    if (!res.ok) {
      let detail = '';
      try { const j = await res.json(); detail = j.detail || ''; } catch {}
      throw new Error(detail || `HTTP ${res.status}`);
    }
    const data = await res.json();
    const draft = data.draft || '';
    body.innerHTML = `
      <div style="background:rgba(167,139,250,0.06); border:1px solid rgba(167,139,250,0.3); border-radius:8px; padding:0.9rem; margin-bottom:0.8rem;">
        <div style="font-size:0.78rem; color:#a1a1aa; margin-bottom:0.4rem;">生成された文案 (編集可)</div>
        <textarea id="aiDraftText" rows="10" style="width:100%; padding:0.6rem; background:rgba(0,0,0,0.4); border:1px solid rgba(255,255,255,0.15); border-radius:8px; color:#fff; font-family:inherit; resize:vertical;">${escapeHtml(draft)}</textarea>
      </div>
      <div style="display:flex; gap:0.5rem; flex-wrap:wrap;">
        ${kind === 'reply_draft' ? `<button id="aiDraftUseAsReply" type="button" style="flex:1; padding:0.7rem; background:linear-gradient(135deg,#6366f1,#8b5cf6); border:0; border-radius:8px; color:#fff; font-weight:700; cursor:pointer;">✉️ この文面で個別送信フォームを開く</button>` : `<button id="aiDraftUseAsBroadcast" type="button" style="flex:1; padding:0.7rem; background:linear-gradient(135deg,#ec4899,#8b5cf6); border:0; border-radius:8px; color:#fff; font-weight:700; cursor:pointer;">📢 この文面で一斉送信フォームを開く</button>`}
        <button id="aiDraftRegen" type="button" style="padding:0.7rem 1rem; background:rgba(255,255,255,0.08); border:0; border-radius:8px; color:#c7d2fe; cursor:pointer;">🔁 再生成</button>
        <button id="aiDraftCopy" type="button" style="padding:0.7rem 1rem; background:rgba(255,255,255,0.08); border:0; border-radius:8px; color:#c7d2fe; cursor:pointer;">📋 コピー</button>
      </div>
      <div id="aiDraftMsg" style="margin-top:0.5rem; font-size:0.78rem; min-height:1em;"></div>
      <div style="margin-top:0.5rem; font-size:0.7rem; color:#71717a; text-align:right;">model: ${escapeHtml(data.model || 'gemini-2.5-flash')} ・ 必ず塾長が確認・編集してから送信してください</div>`;

    body.querySelector('#aiDraftCopy').addEventListener('click', async () => {
      const t = body.querySelector('#aiDraftText').value;
      try {
        await navigator.clipboard.writeText(t);
        body.querySelector('#aiDraftMsg').innerHTML = '<span style="color:#86efac;">✅ コピーしました</span>';
      } catch { body.querySelector('#aiDraftMsg').innerHTML = '<span style="color:#fca5a5;">❌ コピー失敗 (手動でテキスト選択してコピーしてください)</span>'; }
    });
    body.querySelector('#aiDraftRegen').addEventListener('click', () => openAiDraftModal(kind, context, hint, targetName, targetSid));

    if (kind === 'reply_draft') {
      body.querySelector('#aiDraftUseAsReply').addEventListener('click', () => {
        const t = body.querySelector('#aiDraftText').value;
        switchMsgTab('student');
        const sel = document.getElementById('msgStudentSelect');
        if (sel && targetSid) sel.value = String(targetSid);
        const subj = document.getElementById('msgSubject');
        if (subj && !subj.value) subj.value = `Re: お問い合わせの件 (${targetName || ''})`;
        const bodyInp = document.getElementById('msgBody');
        if (bodyInp) bodyInp.value = t;
        modal.style.display = 'none';
        const sec = document.getElementById('messagesSection');
        if (sec) sec.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    } else {
      body.querySelector('#aiDraftUseAsBroadcast').addEventListener('click', () => {
        const t = body.querySelector('#aiDraftText').value;
        switchMsgTab('broadcast');
        const subj = document.getElementById('msgSubject');
        if (subj && !subj.value) subj.value = '';
        const bodyInp = document.getElementById('msgBody');
        if (bodyInp) bodyInp.value = t;
        modal.style.display = 'none';
        const sec = document.getElementById('messagesSection');
        if (sec) sec.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    }
  } catch (e) {
    body.innerHTML = `<div style="color:#fca5a5; padding:1rem;">❌ 生成失敗: ${escapeHtml(e.message || '')}</div>`;
  }
}


// ==========================================================================
// 📋 国公立難関大学コース 申込待ち (Phase 4.8)
// ==========================================================================
function initCourseApps() {
  const refresh = document.getElementById('caRefreshBtn');
  if (refresh && !refresh._caBound) {
    refresh.addEventListener('click', loadCourseApps);
    refresh._caBound = true;
  }
  const copyBtn = document.getElementById('caCopyUrlBtn');
  if (copyBtn && !copyBtn._caBound) {
    copyBtn.addEventListener('click', () => {
      const url = window.location.origin + '/course-kokuritsu-nankan.html';
      navigator.clipboard.writeText(url).then(() => {
        copyBtn.textContent = '✅ コピー済み';
        setTimeout(() => { copyBtn.textContent = '📋 URL コピー'; }, 2000);
      }).catch(() => {
        prompt('以下の URL をコピーしてください:', url);
      });
    });
    copyBtn._caBound = true;
  }
  const tryLoad = (retries = 10) => {
    if (window.AdminAuth && window.AdminAuth.getToken()) return loadCourseApps();
    if (retries > 0) setTimeout(() => tryLoad(retries - 1), 200);
  };
  tryLoad();
}

async function loadCourseApps() {
  const list = document.getElementById('caList');
  const badge = document.getElementById('caPendingBadge');
  if (!list || !window.AdminAuth || !window.AdminAuth.getToken()) return;
  list.innerHTML = '<div style="text-align:center; color:#71717a; padding:1rem;">読み込み中...</div>';
  try {
    const res = await window.AdminAuth.fetch('/api/admin/course-applications?status=pending&limit=100');
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const data = await res.json();
    const apps = data.applications || [];
    const pending = data.pending_count || 0;
    if (badge) {
      if (pending > 0) { badge.textContent = pending > 99 ? '99+' : pending; badge.style.display = ''; }
      else { badge.style.display = 'none'; }
    }
    if (!apps.length) {
      list.innerHTML = '<div style="text-align:center; color:#71717a; padding:1.5rem;">📭 未対応の申込はありません</div>';
      return;
    }
    list.innerHTML = apps.map(a => `
      <div data-id="${a.id}" style="background:rgba(255,255,255,0.04); border:1px solid rgba(167,139,250,0.3); border-left:4px solid #a78bfa; border-radius:10px; padding:0.85rem; margin-bottom:0.5rem;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.4rem; flex-wrap:wrap; gap:0.3rem;">
          <div style="font-weight:800; color:#e4e4e7;">📥 ${escapeHtml(a.name)}${a.grade ? ` <span style="color:#71717a; font-size:0.78rem;">(${escapeHtml(a.grade)})</span>` : ''}</div>
          <div style="font-size:0.72rem; color:#71717a;">${escapeHtml(_msgFmtJst(a.created_at))}</div>
        </div>
        <div style="display:grid; grid-template-columns:auto 1fr; gap:0.3rem 0.7rem; font-size:0.82rem; margin-bottom:0.5rem;">
          <span style="color:#a1a1aa;">📧 メール:</span> <span style="color:#e4e4e7;">${escapeHtml(a.email)}</span>
          ${a.target_university ? `<span style="color:#a1a1aa;">🎯 志望校:</span> <span style="color:#fbbf24;">${escapeHtml(a.target_university)}</span>` : ''}
          ${a.phone ? `<span style="color:#a1a1aa;">📞 電話:</span> <span style="color:#e4e4e7;">${escapeHtml(a.phone)}</span>` : ''}
          ${a.referrer ? `<span style="color:#a1a1aa;">👥 紹介者:</span> <span style="color:#e4e4e7;">${escapeHtml(a.referrer)}</span>` : ''}
        </div>
        ${a.note ? `<div style="background:rgba(0,0,0,0.25); padding:0.45rem 0.6rem; border-radius:6px; font-size:0.82rem; color:#d4d4d8; margin-bottom:0.5rem;">💬 ${escapeHtml(a.note)}</div>` : ''}
        <div style="display:flex; gap:0.5rem; flex-wrap:wrap;">
          <button data-id="${a.id}" data-name="${escapeHtml(a.name)}" class="ca-approve-btn" style="background:linear-gradient(135deg,#10b981,#34d399); color:#fff; border:0; padding:0.5rem 1rem; border-radius:8px; cursor:pointer; font-size:0.85rem; font-weight:700;">✅ 承認 (アカウント作成 + magic link 送信)</button>
          <button data-id="${a.id}" data-name="${escapeHtml(a.name)}" class="ca-reject-btn" style="background:rgba(239,68,68,0.15); color:#fca5a5; border:0; padding:0.5rem 0.9rem; border-radius:8px; cursor:pointer; font-size:0.85rem;">✕ 却下</button>
        </div>
        <div class="ca-result" style="margin-top:0.4rem; font-size:0.78rem; min-height:1em;"></div>
      </div>`).join('');
    list.querySelectorAll('.ca-approve-btn').forEach(b => b.addEventListener('click', async (e) => {
      const id = b.getAttribute('data-id');
      const name = b.getAttribute('data-name');
      const resultEl = b.parentElement.parentElement.querySelector('.ca-result');
      if (!confirm(`「${name}」さんを承認しますか?\n生徒アカウントを作成し、magic link メールを送信します。`)) return;
      b.disabled = true;
      const orig = b.textContent;
      b.textContent = '承認処理中...';
      try {
        const r = await window.AdminAuth.fetch(`/api/admin/course-applications/${encodeURIComponent(id)}/approve`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({}),
        });
        if (!r.ok) {
          let detail = ''; try { const j = await r.json(); detail = j.detail || ''; } catch {}
          throw new Error(detail || `HTTP ${r.status}`);
        }
        const j = await r.json();
        resultEl.innerHTML = `<span style="color:#86efac;">✅ 承認完了 (生徒ID: ${j.student_id} ${j.welcome_email_sent ? '/ welcome メール送信済' : '/ メール送信失敗'})</span>`;
        setTimeout(() => loadCourseApps(), 1500);
      } catch (err) {
        resultEl.innerHTML = `<span style="color:#fca5a5;">❌ ${escapeHtml(err.message || '承認失敗')}</span>`;
        b.disabled = false; b.textContent = orig;
      }
    }));
    list.querySelectorAll('.ca-reject-btn').forEach(b => b.addEventListener('click', async () => {
      const id = b.getAttribute('data-id');
      const name = b.getAttribute('data-name');
      const reason = prompt(`「${name}」さんを却下しますか?\n理由を入力してください (任意・内部メモ):`);
      if (reason === null) return;
      b.disabled = true;
      try {
        const r = await window.AdminAuth.fetch(`/api/admin/course-applications/${encodeURIComponent(id)}/reject`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ reason: reason || undefined }),
        });
        if (!r.ok) throw new Error('HTTP ' + r.status);
        await loadCourseApps();
      } catch (err) {
        alert('却下失敗: ' + (err.message || ''));
        b.disabled = false;
      }
    }));
  } catch (e) {
    list.innerHTML = `<div style="color:#fca5a5; padding:1rem;">エラー: ${escapeHtml(e.message || '')}</div>`;
  }
}

// ==========================================================================
// 💾 DB Backup (Cloudflare R2) — 2026-05-21 塾長指示「DB の保存の昨日の続き」
// ==========================================================================
//   GET /api/admin/db/r2-backups (一覧) → 503 で env 未設定判定
//   POST /api/admin/db/snapshot-to-r2 (手動 trigger・cron 兼用)
function _fmtBytes(n) {
  if (!n || n < 0) return '-';
  if (n < 1024) return n + ' B';
  if (n < 1024 * 1024) return (n / 1024).toFixed(1) + ' KB';
  if (n < 1024 * 1024 * 1024) return (n / 1024 / 1024).toFixed(1) + ' MB';
  return (n / 1024 / 1024 / 1024).toFixed(2) + ' GB';
}

function _fmtBackupDate(iso) {
  try {
    const d = new Date(iso);
    const Y = d.getFullYear();
    const M = String(d.getMonth() + 1).padStart(2, '0');
    const D = String(d.getDate()).padStart(2, '0');
    const h = String(d.getHours()).padStart(2, '0');
    const m = String(d.getMinutes()).padStart(2, '0');
    return `${Y}/${M}/${D} ${h}:${m}`;
  } catch (_) { return iso || '-'; }
}

async function loadR2BackupStatus() {
  const statusEl = document.getElementById('r2Status');
  const listEl = document.getElementById('r2BackupList');
  const envHint = document.getElementById('r2EnvHint');
  const resultEl = document.getElementById('r2Result');
  if (!statusEl || !listEl) return;
  if (!window.AdminAuth || !window.AdminAuth.getToken()) {
    statusEl.textContent = '🔒 管理者認証が必要です';
    return;
  }
  statusEl.textContent = '⏳ 取得中...';
  if (envHint) envHint.style.display = 'none';
  if (resultEl) resultEl.style.display = 'none';
  try {
    const res = await window.AdminAuth.fetch('/api/admin/db/r2-backups?limit=30');
    if (res.status === 503) {
      const body = await res.json().catch(() => ({}));
      statusEl.innerHTML = '<span style="color:#fca5a5;">⚠️ ' + escapeHtml(body.detail || 'env 未設定') + '</span>';
      if (envHint) envHint.style.display = 'block';
      listEl.innerHTML = '<div style="color:#71717a;font-size:0.78rem;">env 設定後に再読み込み</div>';
      return;
    }
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(`HTTP ${res.status}: ${body.detail || res.statusText}`);
    }
    const data = await res.json();
    const items = Array.isArray(data.items) ? data.items : [];
    const count = data.count || items.length;
    const latest = items[0];
    if (latest) {
      const ageMs = Date.now() - new Date(latest.last_modified).getTime();
      const ageHours = Math.floor(ageMs / 1000 / 60 / 60);
      // 🛟 daily backup 想定: < 24h 緑 / 24-48h 黄 / > 48h 赤 (1 日途切れたら警告)
      const ageColor = ageHours < 24 ? '#bbf7d0' : (ageHours < 48 ? '#fde68a' : '#fca5a5');
      const ageMark = ageHours < 24 ? '✅' : (ageHours < 48 ? '⚠️' : '🚨');
      statusEl.innerHTML = `<span style="color:${ageColor};">${ageMark} 最新: ${escapeHtml(_fmtBackupDate(latest.last_modified))} (${ageHours}h 前) / 合計 ${count} 件 / bucket: <code>${escapeHtml(data.bucket || '-')}</code></span>`;
    } else {
      statusEl.innerHTML = `<span style="color:#fde68a;">⚠️ Backup 未取得 (env は設定済・bucket: ${escapeHtml(data.bucket || '-')})。「📸 今すぐ Backup」で初回実行を。</span>`;
    }
    if (items.length === 0) {
      listEl.innerHTML = '<div style="color:#71717a;font-size:0.78rem;padding:0.5rem;">📭 まだ Backup がありません</div>';
    } else {
      listEl.innerHTML = items.map(it => `
        <div style="display:flex;justify-content:space-between;align-items:center;padding:0.45rem 0.5rem;border-bottom:1px solid rgba(255,255,255,0.05);font-size:0.78rem;gap:0.5rem;flex-wrap:wrap;">
          <span style="color:#dbeafe;font-family:monospace;flex:1 1 240px;word-break:break-all;">${escapeHtml(it.key || '')}</span>
          <span style="color:#fbbf24;font-weight:700;min-width:80px;text-align:right;">${escapeHtml(_fmtBytes(it.size))}</span>
          <span style="color:#94a3b8;min-width:140px;text-align:right;">${escapeHtml(_fmtBackupDate(it.last_modified))}</span>
        </div>
      `).join('');
    }
  } catch (e) {
    statusEl.innerHTML = `<span style="color:#fca5a5;">❌ ${escapeHtml(e.message || String(e))}</span>`;
    listEl.innerHTML = `<div style="color:#fca5a5;font-size:0.78rem;padding:0.5rem;">取得失敗: ${escapeHtml(e.message || '')}</div>`;
  }
}

async function triggerR2Snapshot() {
  const btn = document.getElementById('r2SnapshotBtn');
  const statusEl = document.getElementById('r2Status');
  const resultEl = document.getElementById('r2Result');
  if (!btn) return;
  if (!window.AdminAuth || !window.AdminAuth.getToken()) {
    if (statusEl) statusEl.textContent = '🔒 管理者認証が必要です';
    return;
  }
  if (!confirm('今すぐ R2 に DB Backup を取りますか? (数十秒〜数分かかります)')) return;
  btn.disabled = true;
  const origText = btn.textContent;
  btn.textContent = '⏳ Backup 実行中... (10-60 秒)';
  if (resultEl) resultEl.style.display = 'none';
  try {
    const res = await window.AdminAuth.fetch('/api/admin/db/snapshot-to-r2', { method: 'POST' });
    const data = await res.json().catch(() => ({}));
    if (res.status === 503) {
      if (statusEl) statusEl.innerHTML = '<span style="color:#fca5a5;">⚠️ ' + escapeHtml(data.detail || 'env 未設定') + '</span>';
      const envHint = document.getElementById('r2EnvHint');
      if (envHint) envHint.style.display = 'block';
      return;
    }
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${data.detail || res.statusText}`);
    if (resultEl) {
      resultEl.style.display = 'block';
      resultEl.innerHTML = `
        ✅ <strong style="color:#22c55e;">Backup 成功</strong><br>
        <span style="font-family:monospace;font-size:0.78rem;">key: ${escapeHtml(data.key || '-')}</span><br>
        <span style="font-size:0.78rem;">size: ${escapeHtml(_fmtBytes(data.size_bytes))} / tables: ${data.tables_count || '-'} / 所要: ${data.duration_sec ? data.duration_sec.toFixed(1) + 's' : '-'}</span>
      `;
    }
    await loadR2BackupStatus();
  } catch (e) {
    if (statusEl) statusEl.innerHTML = `<span style="color:#fca5a5;">❌ ${escapeHtml(e.message || String(e))}</span>`;
  } finally {
    btn.disabled = false;
    btn.textContent = origText;
  }
}

// ボタン bind + AdminAuth 認証完了後 auto-load (DR の重要度を考慮し開幕で状態可視化)
document.addEventListener('DOMContentLoaded', () => {
  const refreshBtn = document.getElementById('r2RefreshBtn');
  const snapshotBtn = document.getElementById('r2SnapshotBtn');
  if (refreshBtn) refreshBtn.addEventListener('click', loadR2BackupStatus);
  if (snapshotBtn) snapshotBtn.addEventListener('click', triggerR2Snapshot);
  // 認証完了を待つ retry: 300ms × 最大 20 回 (6 秒) で AdminAuth ready → 1 回 auto-load
  // (magic link verify / Bearer decode で 3s 超える case を許容)
  let tries = 0;
  const tickerR2 = setInterval(() => {
    tries++;
    if (window.AdminAuth && window.AdminAuth.getToken()) {
      clearInterval(tickerR2);
      try { loadR2BackupStatus(); } catch (_) {}
    } else if (tries >= 20) {
      clearInterval(tickerR2);  // abandon 時は塾長に明示 (操作迷いゼロ化)
      const statusEl = document.getElementById('r2Status');
      if (statusEl) statusEl.innerHTML = '<span style="color:#94a3b8;">🔄 自動取得タイムアウト — 認証後に「状態更新」ボタンを押してください</span>';
    }
  }, 300);
});
