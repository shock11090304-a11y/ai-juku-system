// ==========================================================================
// Campaign Command Center — 3-phase execution dashboard
// ==========================================================================

const KEYS = {
  CK: 'ai_juku_campaign_checklist',
  FOUNDER: 'ai_juku_founder_count',
  CAMPAIGN_STATS: 'ai_juku_campaign_stats',
};

const PHASES = [
  { id: 1, name: '創設メンバー (永年¥14,500/月)', price: 14500, start: 0,  end: 50,  discount: '永年' },
  { id: 2, name: '第2期生',                       price: 29800, start: 50, end: 250, discount: '値上げ' },
  { id: 3, name: '第3期生',                       price: 34800, start: 250, end: 450, discount: '値上げ' },
  { id: 4, name: '通常',                          price: null,  start: 450, end: Infinity, discount: null },
];

function getCurrentCount() {
  return parseInt(localStorage.getItem(KEYS.FOUNDER) || '32');
}

function getCurrentPhase(count) {
  for (const p of PHASES) {
    if (count >= p.start && count < p.end) return p;
  }
  return PHASES[PHASES.length - 1];
}

function render() {
  const count = getCurrentCount();
  const phase = getCurrentPhase(count);
  const now = new Date();

  document.getElementById('updateTime').textContent =
    `${now.getMonth() + 1}/${now.getDate()} ${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}`;
  document.getElementById('currentPhase').textContent = `Phase ${phase.id}`;

  // Phase progress bars
  [1, 2, 3].forEach(pid => {
    const p = PHASES[pid - 1];
    const cnt = Math.max(0, Math.min(p.end - p.start, count - p.start));
    const pct = (cnt / (p.end - p.start)) * 100;
    document.getElementById(`phase${pid}Fill`).style.width = `${pct}%`;
    document.getElementById(`phase${pid}Count`).textContent = cnt;
    const stage = document.querySelector(`[data-phase="${pid}"]`);
    if (stage) {
      stage.classList.toggle('active', phase.id === pid);
      stage.classList.toggle('done', pid < phase.id);
    }
  });

  // Phase sections active state
  document.querySelectorAll('.camp-phase').forEach((sec, i) => {
    sec.classList.toggle('active', i + 1 === phase.id || phase.id === 1);
  });

  // KPIs
  const remaining = Math.max(0, 50 - count);
  document.getElementById('kpiRemaining').textContent = remaining;

  const stats = JSON.parse(localStorage.getItem(KEYS.CAMPAIGN_STATS) || '{}');
  const today = now.toISOString().slice(0, 10);
  const weekAgo = new Date(now - 7 * 86400000).toISOString().slice(0, 10);
  const todayCount = stats[today] || 0;
  let weekCount = 0;
  Object.entries(stats).forEach(([d, c]) => {
    if (d >= weekAgo) weekCount += c;
  });
  document.getElementById('kpiToday').textContent = todayCount;
  document.getElementById('kpiWeek').textContent = weekCount;

  // Revenue calculations
  // 体験は完全無料なので体験売上はゼロ。本契約 (founder_special) ベースで月次収益を試算する。
  const expectedPaid = Math.round(count * 0.4); // 体験→本契約の想定転換率 40%
  const founderSpecialMrr = expectedPaid * 14500; // 創設メンバープラン永年¥14,500/月
  document.getElementById('kpiRevenue').textContent = '¥0';
  document.getElementById('kpiMrr').textContent = `¥${founderSpecialMrr.toLocaleString()}`;

  // Checklist
  const ck = JSON.parse(localStorage.getItem(KEYS.CK) || '{}');
  document.querySelectorAll('[data-ck]').forEach(input => {
    input.checked = !!ck[input.dataset.ck];
  });
}

// Checklist persistence
function bindChecklist() {
  document.querySelectorAll('[data-ck]').forEach(input => {
    input.addEventListener('change', () => {
      const ck = JSON.parse(localStorage.getItem(KEYS.CK) || '{}');
      ck[input.dataset.ck] = input.checked;
      localStorage.setItem(KEYS.CK, JSON.stringify(ck));
    });
  });
}

// Open outreach tool with fee tier filter
function openOutreachWithFilter(tier) {
  window.location.href = `personalized-outreach.html?tier=${tier}`;
}
window.openOutreachWithFilter = openOutreachWithFilter;

// Forecast chart
function renderForecast() {
  const ctx = document.getElementById('forecastChart');
  if (!ctx) return;
  Chart.defaults.color = '#9ca3af';
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: ['今', '1ヶ月後', '2ヶ月後', '3ヶ月後'],
      datasets: [
        {
          label: 'MRR (月商)',
          data: [0, 1592000, 3184000, 4284000],
          borderColor: '#818cf8',
          backgroundColor: 'rgba(129, 140, 248, 0.15)',
          tension: 0.3,
          fill: true,
        },
        {
          label: '累計純利益',
          data: [0, 1500000, 3300000, 4950000],
          borderColor: '#10b981',
          backgroundColor: 'rgba(16, 185, 129, 0.15)',
          tension: 0.3,
          fill: true,
        },
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { position: 'top' },
        tooltip: {
          callbacks: {
            label: (c) => `${c.dataset.label}: ¥${c.parsed.y.toLocaleString()}`
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: { callback: (v) => '¥' + (v / 10000).toFixed(0) + '万' }
        }
      }
    }
  });
}

document.addEventListener('DOMContentLoaded', () => {
  render();
  bindChecklist();
  renderForecast();

  document.getElementById('openOutreach')?.addEventListener('click', () => {
    window.location.href = 'personalized-outreach.html';
  });
  document.getElementById('openAdsKit')?.addEventListener('click', () => {
    window.location.href = 'ad-variations.html';
  });

  // Auto-refresh: タブ表示時のみ（バックグラウンド時は停止）
  let refreshTimer = null;
  const startAutoRefresh = () => {
    if (refreshTimer) return;
    refreshTimer = setInterval(render, 60000);
  };
  const stopAutoRefresh = () => {
    if (refreshTimer) { clearInterval(refreshTimer); refreshTimer = null; }
  };
  document.addEventListener('visibilitychange', () => {
    document.hidden ? stopAutoRefresh() : startAutoRefresh();
  });
  if (!document.hidden) startAutoRefresh();
});
