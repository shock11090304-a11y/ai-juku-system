// ==========================================================================
// Auto-Alert System — 非活動検知・段階的エスカレーション・配信管理
// ==========================================================================

const KEYS = {
  CONFIG: 'ai_juku_alert_config',
  ACTIVITY: 'ai_juku_activity_log',
  LOG: 'ai_juku_notification_log',
  PARENT_PREF: 'ai_juku_parent_pref',
};

const DEFAULTS = {
  level1Days: 3,
  level2Days: 5,
  level3Days: 7,
  ruleQuestCount: true,
  ruleMoshiUpload: true,
  ruleWeeklyReport: true,
  ruleCelebration: true,
  ruleTestWeek: false,
  ruleQuiet: false,
  parentFreq: 'important',
};

function loadConfig() {
  const saved = JSON.parse(localStorage.getItem(KEYS.CONFIG) || '{}');
  return { ...DEFAULTS, ...saved };
}

function saveConfig(cfg) {
  localStorage.setItem(KEYS.CONFIG, JSON.stringify(cfg));
}

// ==========================================================================
// Sample inactive students (in production, would come from /api/alerts/check)
// ==========================================================================
function getInactiveStudents() {
  const config = loadConfig();
  // Use juku-manager-data.json + simulate some as inactive
  const sample = [
    { id: 1, name: '山田 太郎', grade: '高校2年', daysInactive: 2, level: 'ok' },
    { id: 2, name: '佐藤 花子', grade: '中学3年', daysInactive: 4, level: 'level-1' },
    { id: 3, name: '鈴木 一郎', grade: '高校3年', daysInactive: 6, level: 'level-2' },
    { id: 4, name: '田中 美咲', grade: '中学2年', daysInactive: 8, level: 'level-3' },
    { id: 5, name: '伊藤 健太', grade: '高校1年', daysInactive: 3, level: 'level-1' },
    { id: 6, name: '渡辺 あゆみ', grade: '高校3年', daysInactive: 10, level: 'level-3' },
    { id: 7, name: '小林 優斗', grade: '中学2年', daysInactive: 5, level: 'level-2' },
  ];

  return sample.map(s => {
    let level = 'ok';
    if (s.daysInactive >= config.level3Days) level = 'level-3';
    else if (s.daysInactive >= config.level2Days) level = 'level-2';
    else if (s.daysInactive >= config.level1Days) level = 'level-1';
    return { ...s, level };
  }).filter(s => s.level !== 'ok');
}

function avatarFor(name) {
  if (/花|美|結|あゆみ|ゆか|咲|奈|愛/i.test(name)) return '👧';
  return '🧑';
}

function renderInactive(filter = 'all') {
  const students = getInactiveStudents();
  const filtered = filter === 'all' ? students : students.filter(s => s.level === filter);
  const container = document.getElementById('inactiveList');

  if (filtered.length === 0) {
    container.innerHTML = '<p style="text-align:center;padding:2rem;color:var(--text-muted);">要注意の生徒はいません ✨</p>';
    return;
  }

  container.innerHTML = filtered.map(s => `
    <div class="inactive-item ${s.level.replace('level-', 'lv')}">
      <div class="inactive-avatar">${avatarFor(s.name)}</div>
      <div class="inactive-info">
        <div class="name">${s.name}</div>
        <div class="meta">${s.grade}</div>
      </div>
      <div class="inactive-days">${s.daysInactive}<small>日未学習</small></div>
      <div class="inactive-preview">${s.level === 'level-3' ? '🔴 介入要請' : s.level === 'level-2' ? '🟠 併走アラート' : '🟡 ソフトリマインド'}</div>
      <button class="inactive-action" onclick="sendNowFor(${s.id}, '${s.level}')">✉️ 今すぐ通知</button>
    </div>
  `).join('');
}

function sendNowFor(studentId, level) {
  logNotification({
    time: new Date(),
    level,
    content: `生徒ID:${studentId} に${level}通知を手動送信`,
    status: 'sent',
  });
  alert(`✅ 通知を送信しました\n\n※バックエンド未接続時はログのみ記録されます。\n本番環境では LINE/メールに実配信されます。`);
  renderLog();
}

// ==========================================================================
// Notification log
// ==========================================================================
function logNotification(entry) {
  const log = JSON.parse(localStorage.getItem(KEYS.LOG) || '[]');
  log.unshift({ ...entry, time: entry.time.toISOString() });
  localStorage.setItem(KEYS.LOG, JSON.stringify(log.slice(0, 50)));
}

function renderLog() {
  let log = JSON.parse(localStorage.getItem(KEYS.LOG) || '[]');

  if (log.length === 0) {
    // Seed with sample data
    const now = Date.now();
    log = [
      { time: new Date(now - 3600000 * 1).toISOString(), level: 'summary', content: '日曜20時の週次サマリー 保護者92名に配信', status: 'sent' },
      { time: new Date(now - 3600000 * 3).toISOString(), level: 'lv1', content: '佐藤花子さん (3日未学習) 本人に優しいリマインド', status: 'sent' },
      { time: new Date(now - 3600000 * 8).toISOString(), level: 'lv2', content: '鈴木一郎さん (5日未学習) 生徒+保護者にアラート', status: 'sent' },
      { time: new Date(now - 3600000 * 26).toISOString(), level: 'lv3', content: '渡辺あゆみさん (10日未学習) メンター介入要請', status: 'sent' },
      { time: new Date(now - 3600000 * 30).toISOString(), level: 'celebration', content: '山田太郎さん 7日連続ストリーク達成！保護者に褒める通知', status: 'sent' },
      { time: new Date(now - 3600000 * 48).toISOString(), level: 'lv1', content: '伊藤健太さん (3日未学習) リマインド', status: 'sent' },
      { time: new Date(now - 3600000 * 72).toISOString(), level: 'summary', content: '月初の模試アップロード依頼 保護者103名に配信', status: 'sent' },
    ];
    localStorage.setItem(KEYS.LOG, JSON.stringify(log));
  }

  const container = document.getElementById('notificationLog');
  container.innerHTML = log.slice(0, 20).map(e => {
    const time = new Date(e.time);
    const timeStr = `${time.getMonth() + 1}/${time.getDate()} ${String(time.getHours()).padStart(2,'0')}:${String(time.getMinutes()).padStart(2,'0')}`;
    const levelText = { lv1: '🟡 Lv1', lv2: '🟠 Lv2', lv3: '🔴 Lv3', summary: '📊 Summary', celebration: '🎉 祝', 'level-1': '🟡 Lv1', 'level-2': '🟠 Lv2', 'level-3': '🔴 Lv3' }[e.level] || e.level;
    return `
      <div class="log-entry">
        <div class="log-time">${timeStr}</div>
        <div class="log-level ${e.level.replace('level-', 'lv')}">${levelText}</div>
        <div class="log-content">${e.content}</div>
        <div class="log-status ${e.status}">${e.status === 'sent' ? '✓ 配信' : '✗ 失敗'}</div>
      </div>
    `;
  }).join('');
}

// ==========================================================================
// Test dispatch
// ==========================================================================
async function sendTest() {
  const type = document.getElementById('testType').value;
  const dest = document.getElementById('testDestination').value.trim();
  const resultEl = document.getElementById('testResult');

  if (!dest) {
    resultEl.className = 'test-result error';
    resultEl.style.display = 'block';
    resultEl.textContent = '❌ 送信先を入力してください';
    return;
  }

  resultEl.className = 'test-result';
  resultEl.style.display = 'block';
  resultEl.textContent = '⏳ 送信中...';

  // Backend check
  try {
    const BACKEND = window.location.hostname === 'localhost' && window.location.port === '8090'
      ? 'http://localhost:8000' : window.location.origin;
    const res = await fetch(`${BACKEND}/api/alerts/test`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type, destination: dest }),
    });
    if (!res.ok) throw new Error('Backend not available');
    resultEl.className = 'test-result success';
    resultEl.textContent = `✅ ${dest} にテスト送信しました`;
  } catch (e) {
    resultEl.className = 'test-result success';
    resultEl.textContent = `✅ (ローカルモック) ${dest} 宛の「${document.getElementById('testType').selectedOptions[0].textContent}」を準備しました。バックエンド稼働時は実送信されます。`;
  }

  logNotification({
    time: new Date(),
    level: type.startsWith('level1') ? 'lv1' : type.startsWith('level2') ? 'lv2' : type.startsWith('level3') ? 'lv3' : 'summary',
    content: `テスト配信 → ${dest}`,
    status: 'sent',
  });
  renderLog();
}

// ==========================================================================
// Init & event bindings
// ==========================================================================
document.addEventListener('DOMContentLoaded', () => {
  const config = loadConfig();

  // Init range sliders
  ['level1', 'level2', 'level3'].forEach(lv => {
    const range = document.getElementById(`${lv}Range`);
    const label = document.getElementById(`${lv}Days`);
    range.value = config[`${lv}Days`];
    label.textContent = config[`${lv}Days`];
    range.addEventListener('input', () => {
      label.textContent = range.value;
      config[`${lv}Days`] = parseInt(range.value);
      saveConfig(config);
      renderInactive();
    });
  });

  // Init rule switches
  ['ruleQuestCount', 'ruleMoshiUpload', 'ruleWeeklyReport', 'ruleCelebration', 'ruleTestWeek', 'ruleQuiet'].forEach(rule => {
    const el = document.getElementById(rule);
    if (!el) return;
    el.checked = config[rule];
    el.addEventListener('change', () => {
      config[rule] = el.checked;
      saveConfig(config);
    });
  });

  // Parent pref
  const pref = JSON.parse(localStorage.getItem(KEYS.PARENT_PREF) || '"important"');
  const radio = document.querySelector(`input[name="parentFreq"][value="${pref}"]`);
  if (radio) radio.checked = true;
  document.querySelectorAll('input[name="parentFreq"]').forEach(r => {
    r.addEventListener('change', () => {
      if (r.checked) localStorage.setItem(KEYS.PARENT_PREF, JSON.stringify(r.value));
    });
  });

  // Monitor filters
  document.querySelectorAll('.mon-filter').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.mon-filter').forEach(b => b.classList.toggle('active', b === btn));
      renderInactive(btn.dataset.level);
    });
  });

  // Test dispatch
  document.getElementById('sendTestBtn').addEventListener('click', sendTest);

  // Initial render
  renderInactive();
  renderLog();
});
