// ==========================================================================
// 個別展開ツール — juku-manager 103名へパーソナライズされたメッセージ生成
// ==========================================================================

const STORAGE_STATUS = 'ai_juku_outreach_status';
const STORAGE_NOTES = 'ai_juku_outreach_notes';
let allStudents = [];
let filteredStudents = [];

// ==========================================================================
// Data loading
// ==========================================================================
async function loadStudents() {
  // 🚨 SECURITY: juku-manager-data.json は public 配信禁止 (個人情報・氏名/学年/月謝)
  // 旧来の `fetch('juku-manager-data.json')` は本番で 213名分の個人情報を全公開していた
  // ため削除。admin token 認証付き API 経由でのみ取得する。

  // 1. Backend API (admin 認証必須)
  try {
    const adminTok = localStorage.getItem('ai_juku_admin_token');
    if (adminTok) {
      const backend = (window.location.hostname === 'localhost' && window.location.port === '8090')
        ? 'http://localhost:8000' : window.location.origin;
      const res = await fetch(`${backend}/api/admin/stats`, {
        headers: { 'Authorization': 'Bearer ' + adminTok }
      });
      if (res.ok) {
        const stats = await res.json();
        // /api/admin/stats から取れる students を juku-manager 形式に変換
        const data = { students: (stats.students || []).map(s => ({
          id: s.id, name: s.name, grade: s.grade, email: s.email,
          courses: [], totalFee: 0  // 月謝情報は本番DBにないので空
        })) };
        processData(data);
        updateStatus('🟢 データ取得完了 (admin)', 'live');
        return true;
      }
    }
  } catch (e) {}

  // 2. Local juku-manager server (開発時のみ・CORS可能なら)
  try {
    const res = await fetch('http://localhost:8080/default_data.json');
    if (!res.ok) throw new Error('fetch failed');
    const data = await res.json();
    processData(data);
    updateStatus('🟢 自動取得 (juku-manager)', 'live');
    return true;
  } catch (e) {
    console.log('Auto-load failed:', e.message);
    updateStatus('🟡 ファイル選択が必要', 'demo');
    document.getElementById('loadModal').classList.add('show');
    return false;
  }
}

function processData(data) {
  const students = (data.students || []).filter(s => s.status === '通塾' && s.name);
  allStudents = students.map(s => ({
    id: s.id,
    name: s.name,
    grade: s.grade || '未設定',
    courses: Array.isArray(s.courses) ? s.courses : [],
    fee: s.fee || 0,
    email: s.email || '',
    enrollDate: s.enrollDate || '',
    notes: s.notes || '',
  }));
  // 月謝高い順にソート（第1期生獲得の優先度順）
  allStudents.sort((a, b) => (b.fee || 0) - (a.fee || 0));

  // URLパラメータで自動フィルター適用（campaign.html からの遷移用）
  const params = new URLSearchParams(window.location.search);
  const tierParam = params.get('tier');
  if (tierParam) {
    setTimeout(() => {
      const sel = document.getElementById('feeFilter');
      if (sel) {
        sel.value = tierParam;
        sel.dispatchEvent(new Event('change'));
      }
    }, 100);
  }

  renderStudents();
}

function updateStatus(text, className) {
  const el = document.getElementById('loadStatus');
  el.textContent = text;
  el.className = 'mode-badge' + (className === 'live' ? ' live' : ' demo');
}

// ==========================================================================
// Tier classification
// ==========================================================================
function getTier(fee) {
  if (fee < 10000) return { tier: 'low', name: 'AI Lite', addFee: 1000, label: 'Lite' };
  if (fee < 20000) return { tier: 'mid', name: 'AI Plus', addFee: 3000, label: 'Plus' };
  return { tier: 'high', name: 'AI Pro', addFee: 0, label: 'Pro' };
}

// ==========================================================================
// Message generation (course-aware personalization)
// ==========================================================================
function generateMessage(student) {
  const tier = getTier(student.fee);
  const courses = student.courses || [];
  const courseText = courses.join('・') || '受講中のコース';

  // Identify primary focus from courses
  const focus = detectFocus(courses);
  const benefits = getBenefitsForFocus(focus);
  const isParent = isParentAudience(student.grade);
  const honorific = isParent ? '保護者様' : 'さん';
  const nameWithHonor = `${student.name} ${honorific}`;

  // Tier-specific offer
  const offerText = tier.addFee === 0
    ? `\n既存コース料金に<strong>追加料金¥0</strong>でご提供できます。`
    : `\n既存コース料金に<strong>月¥${tier.addFee.toLocaleString()}</strong>の追加でご利用いただけます（初月無料）。`;

  // Course-specific intro
  let intro, focusBenefit;
  if (focus === 'eiken_jun1') {
    intro = `${student.name}さんが取り組んでいる英検準1級対策について、朗報があります。`;
    focusBenefit = `英検準1級ライティング添削をAIで<strong>無制限</strong>に行えるようになります。\n合格に必要な「添削30回」を、1ヶ月で達成できます。`;
  } else if (focus === 'kokkouritsu') {
    intro = `${student.name}さんが挑戦している国公立難関大受験。AIで加速させる機能を追加しました。`;
    focusBenefit = `赤本添削・志望校別カリキュラム・24時間質問対応が<strong>無制限</strong>に。\n過去問演習の回転数が2-3倍になります。`;
  } else if (focus === 'koukou_bunpou') {
    intro = `${student.name}さんの高校英文法の学習を、AIでさらに効率化できます。`;
    focusBenefit = `Vintage / Next Stage レベルの英文法を<strong>AI質問し放題</strong>。\nわからない例文も24時間いつでも解説してもらえます。`;
  } else if (focus === 'chu_eibunpou') {
    intro = `${student.name}さんが学んでいる中学英文法について、AIサポートを強化しました。`;
    focusBenefit = `基礎英文法を<strong>いつでもAIに質問</strong>できます。\n夜の宿題で詰まっても、その場で解説が聞けます。`;
  } else if (focus === 'bunpou_level1') {
    intro = `${student.name}さんの英文法基礎学習をAIで後押しできます。`;
    focusBenefit = `わからない英文法をいつでも質問、類題を自動生成して練習量も倍に。`;
  } else if (focus === 'kanri_monitor') {
    intro = `${student.name}さんの学習管理モニターコースに最適なAI機能を追加しました。`;
    focusBenefit = `<strong>AI学習診断</strong>で弱点を自動特定、<strong>カリキュラムAI自動生成</strong>で計画立案を秒単位で。\n自学自習の質が劇的に高まります。`;
  } else if (focus === 'choubun') {
    intro = `${student.name}さんの英語長文学習をAIで加速できます。`;
    focusBenefit = `長文の知らない単語や構文も、<strong>AIにその場で質問</strong>して即解説。\n読解スピードが着実に上がります。`;
  } else {
    intro = `${student.name}さんの学習をさらに支援する新機能を追加しました。`;
    focusBenefit = `AIチューターが24時間あなたの質問に答えます。\nわからない問題をその場で解決できる環境です。`;
  }

  // Full message body
  const body = `${isParent ? nameWithHonor : student.name}さん、こんにちは。
〇〇塾の〇〇です。

${intro}

${focusBenefit}

【追加される機能】
${benefits.map(b => `・${b}`).join('\n')}

【🎖 第1期生 優先権】
創業記念・先着100名限定の第1期生枠を、既存生徒さんに優先的にご案内しています。

【トライアル料金】¥0 (7日間 完全無料・クレカ登録不要)
・7日間 全機能使い放題
・継続のお申込みをしなければ7日後に体験は自動終了し、月額課金は一切なし
・第1期生限定特典: 3人紹介で永久50%OFF

【開始方法】
下記URLから30秒で登録できます👇
https://ai-juku.jp/lp.html?ref=existing_${student.id}

ご質問・ご不明点があれば、このメッセージに返信か、お気軽にLINEでお問い合わせください。

〇〇塾
〇〇`;

  // Subject line
  const subject = `【〇〇塾】${student.name}${isParent ? '様' : 'さん'}のためのAIサポート機能のご案内`;

  // Short LINE version
  const lineMsg = `${student.name}さん、こんにちは📘

AI学習サポート機能が使えるようになりました🤖

${focusBenefit.replace(/<strong>/g, '').replace(/<\/strong>/g, '').substring(0, 80)}...

追加料金: ${tier.addFee === 0 ? '¥0（既存料金に含む）' : `月¥${tier.addFee.toLocaleString()} (初月無料)`}

登録URL👇
https://ai-juku.jp/lp.html?ref=existing_${student.id}

質問はいつでも！`;

  return { subject, body, lineMsg, tier, focus };
}

function detectFocus(courses) {
  const cs = courses.join(' ').toLowerCase();
  if (/英検.?準?1級/.test(cs) || cs.includes('準１級') || cs.includes('準1級')) return 'eiken_jun1';
  if (/国公立|難関大/.test(cs)) return 'kokkouritsu';
  if (/学習管理|モニター/.test(cs)) return 'kanri_monitor';
  if (/高校.?2年.?英文法|高２英文法|高2英文法/.test(cs)) return 'koukou_bunpou';
  if (/月曜中.?3|中３英文法|中3英文法/.test(cs)) return 'chu_eibunpou';
  if (/英文法.?レベル/.test(cs)) return 'bunpou_level1';
  if (/長文/.test(cs)) return 'choubun';
  if (/英文解釈/.test(cs)) return 'koukou_bunpou';
  if (/中学/.test(cs)) return 'chu_eibunpou';
  return 'general';
}

function getBenefitsForFocus(focus) {
  const common = ['💬 24時間AIチューター（いつでも質問可能）'];
  const specific = {
    eiken_jun1: ['✍️ AI英作文添削（1日5本の演習可能）', '🎙 面接対策AI（音声で2次試験練習）', '📊 週次ライティング進捗レポート'],
    kokkouritsu: ['📝 赤本・過去問の無制限添削', '🎯 志望校別カリキュラム自動生成', '📷 模試Vision AI（写真から自動採点分析）'],
    koukou_bunpou: ['✍️ 英作文添削無制限', '🧪 オリジナル英文法問題の自動生成', '📊 弱点自動特定'],
    chu_eibunpou: ['🧪 中学英文法問題の無限生成', '📈 毎週の保護者レポート', '🎮 ゲーミフィケーション（XP・ストリーク）'],
    bunpou_level1: ['🧪 レベル別の練習問題自動生成', '📈 学習進捗の可視化'],
    kanri_monitor: ['📊 AI学習診断レポート（毎週）', '🎯 志望校別カリキュラムAI自動生成', '📈 保護者レポート自動配信'],
    choubun: ['📝 英文の語彙・文法をその場で質問', '🧪 類題生成', '⏱ 時間配分のAI提案'],
    general: ['📊 AI学習診断（週次）', '🎯 カリキュラム自動生成', '📈 保護者レポート'],
  };
  return [...common, ...(specific[focus] || specific.general)];
}

function isParentAudience(grade) {
  return grade.includes('小学') || grade.includes('中学1年') || grade.includes('中学2年');
}

// ==========================================================================
// Render
// ==========================================================================
function getStatus(studentId) {
  const all = JSON.parse(localStorage.getItem(STORAGE_STATUS) || '{}');
  return all[studentId] || 'not_sent';
}

function setStatus(studentId, status) {
  const all = JSON.parse(localStorage.getItem(STORAGE_STATUS) || '{}');
  all[studentId] = status;
  localStorage.setItem(STORAGE_STATUS, JSON.stringify(all));
  updateOverview();
}

function getNote(studentId) {
  const all = JSON.parse(localStorage.getItem(STORAGE_NOTES) || '{}');
  return all[studentId] || '';
}

function setNote(studentId, note) {
  const all = JSON.parse(localStorage.getItem(STORAGE_NOTES) || '{}');
  all[studentId] = note;
  localStorage.setItem(STORAGE_NOTES, JSON.stringify(all));
}

function updateOverview() {
  const total = filteredStudents.length;
  let sent = 0, replied = 0, paid = 0;
  filteredStudents.forEach(s => {
    const status = getStatus(s.id);
    if (status === 'sent' || status === 'replied' || status === 'paid') sent++;
    if (status === 'replied' || status === 'paid') replied++;
    if (status === 'paid') paid++;
  });
  document.getElementById('totalCount').textContent = total;
  document.getElementById('sentCount').textContent = sent;
  document.getElementById('repliedCount').textContent = replied;
  document.getElementById('paidCount').textContent = paid;
  const rate = sent > 0 ? Math.round((paid / sent) * 100) : 0;
  document.getElementById('conversionRate').textContent = `${rate}%`;
}

function avatarFor(student) {
  const name = student.name || '';
  if (/花|美|結|あゆみ|ゆか|咲|奈|里|愛|香|優|ノリ|mam|char|kirara|hono|ayu|mim|sana|saki|yuka|emi/i.test(name)) return '👧';
  if (student.grade.includes('中学')) return '🧒';
  if (student.grade.includes('高校')) return '👦';
  return '🧑';
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c]));
}

function renderStudents() {
  applyFilters();
  const list = document.getElementById('studentList');

  if (filteredStudents.length === 0) {
    list.innerHTML = '<div class="loading-state">該当する生徒がいません</div>';
    updateOverview();
    return;
  }

  list.innerHTML = filteredStudents.map(student => {
    const tier = getTier(student.fee);
    const msg = generateMessage(student);
    const status = getStatus(student.id);
    const note = getNote(student.id);
    const avatar = avatarFor(student);
    const statusLabels = { not_sent: '未送信', sent: '送信済み', replied: '返信あり', paid: '登録完了' };

    return `
      <div class="student-row status-${status}" data-id="${student.id}">
        <div class="student-summary" onclick="toggleRow(${student.id})">
          <label class="student-check" onclick="event.stopPropagation()">
            <input type="checkbox" data-select="${student.id}">
          </label>
          <div class="student-avatar">${avatar}</div>
          <div class="student-info">
            <div class="student-name">${escapeHtml(student.name)}</div>
            <div class="student-grade">${escapeHtml(student.grade)}</div>
          </div>
          <div class="student-courses">
            ${(student.courses || []).slice(0, 4).map(c => `<span class="course-chip" title="${escapeHtml(c)}">${escapeHtml(c)}</span>`).join('')}
          </div>
          <div class="student-fee ${tier.tier}">¥${student.fee.toLocaleString()}</div>
          <div class="student-tier tier-${tier.label.toLowerCase()}">${tier.label}</div>
          <div class="student-status ${status}">${statusLabels[status]}</div>
          <div class="student-expand">▼</div>
        </div>
        <div class="student-detail">
          <div class="detail-tabs">
            <button class="detail-tab active" onclick="switchDetailTab(${student.id}, 'email')">📧 メール</button>
            <button class="detail-tab" onclick="switchDetailTab(${student.id}, 'line')">💚 LINE</button>
            <button class="detail-tab" onclick="switchDetailTab(${student.id}, 'status')">📊 ステータス</button>
          </div>

          <div class="detail-content active" data-type="email">
            <div class="message-subject">${escapeHtml(msg.subject)}</div>
            <div class="message-box">${msg.body}</div>
            <div class="message-actions">
              <button class="msg-btn" onclick="copyMessage(${student.id}, 'email')">📋 メール全文をコピー</button>
              <button class="msg-btn secondary" onclick="copySubject(${student.id})">📋 件名のみコピー</button>
              ${student.email ? `<a class="msg-btn secondary" href="mailto:${student.email}?subject=${encodeURIComponent(msg.subject)}&body=${encodeURIComponent(msg.body.replace(/<[^>]+>/g, ''))}">📧 メール作成</a>` : ''}
              <button class="msg-btn success" onclick="markAndNext(${student.id})">✅ 送信済み & 次へ</button>
            </div>
          </div>

          <div class="detail-content" data-type="line">
            <div class="message-box">${escapeHtml(msg.lineMsg)}</div>
            <div class="message-actions">
              <button class="msg-btn" onclick="copyMessage(${student.id}, 'line')">📋 LINE文をコピー</button>
              <button class="msg-btn line" onclick="openLine(${student.id})">💚 LINEで開く</button>
              <button class="msg-btn success" onclick="markAndNext(${student.id})">✅ 送信済み & 次へ</button>
            </div>
          </div>

          <div class="detail-content" data-type="status">
            <div class="status-buttons">
              <button class="status-btn ${status === 'not_sent' ? 'active' : ''}" onclick="updateStatus2(${student.id}, 'not_sent')">⭕ 未送信</button>
              <button class="status-btn ${status === 'sent' ? 'active' : ''}" onclick="updateStatus2(${student.id}, 'sent')">📤 送信済み</button>
              <button class="status-btn ${status === 'replied' ? 'active' : ''}" onclick="updateStatus2(${student.id}, 'replied')">💬 返信あり</button>
              <button class="status-btn ${status === 'paid' ? 'paid-active' : ''}" onclick="updateStatus2(${student.id}, 'paid')">🎉 登録完了</button>
            </div>
            <div style="margin-top:1rem;">
              <label style="display:block;font-size:0.8rem;color:var(--text-dim);margin-bottom:0.4rem;">メモ（返信内容・特記事項など）</label>
              <textarea class="note-textarea" data-note="${student.id}" placeholder="例: 2026-04-22 返信あり、体験開始に同意">${escapeHtml(note)}</textarea>
            </div>
          </div>
        </div>
      </div>
    `;
  }).join('');

  // Bind note auto-save
  document.querySelectorAll('[data-note]').forEach(ta => {
    ta.addEventListener('input', (e) => {
      setNote(parseInt(e.target.dataset.note), e.target.value);
    });
  });

  updateOverview();
}

// ==========================================================================
// Actions
// ==========================================================================
function toggleRow(id) {
  const row = document.querySelector(`.student-row[data-id="${id}"]`);
  if (row) row.classList.toggle('expanded');
}

function switchDetailTab(id, type) {
  const row = document.querySelector(`.student-row[data-id="${id}"]`);
  if (!row) return;
  row.querySelectorAll('.detail-tab').forEach(t => t.classList.remove('active'));
  event.target.classList.add('active');
  row.querySelectorAll('.detail-content').forEach(c => {
    c.classList.toggle('active', c.dataset.type === type);
  });
}

function copyMessage(id, type) {
  const student = allStudents.find(s => s.id === id);
  if (!student) return;
  const msg = generateMessage(student);
  const text = type === 'email'
    ? `件名: ${msg.subject}\n\n${msg.body.replace(/<[^>]+>/g, '')}`
    : msg.lineMsg;
  navigator.clipboard.writeText(text).then(() => {
    if (event.target) {
      event.target.textContent = '✅ コピーしました';
      setTimeout(() => event.target.textContent = type === 'email' ? '📋 メール全文をコピー' : '📋 LINE文をコピー', 1500);
    }
  });
}

function copySubject(id) {
  const student = allStudents.find(s => s.id === id);
  if (!student) return;
  const msg = generateMessage(student);
  navigator.clipboard.writeText(msg.subject).then(() => {
    if (event.target) {
      event.target.textContent = '✅ コピー済';
      setTimeout(() => event.target.textContent = '📋 件名のみコピー', 1500);
    }
  });
}

function openLine(id) {
  const student = allStudents.find(s => s.id === id);
  if (!student) return;
  const msg = generateMessage(student);
  window.open(`https://line.me/R/share?text=${encodeURIComponent(msg.lineMsg)}`);
}

function updateStatus2(id, status) {
  setStatus(id, status);
  renderStudents();
}

function markAndNext(id) {
  setStatus(id, 'sent');
  const current = filteredStudents.findIndex(s => s.id === id);
  const next = filteredStudents[current + 1];
  renderStudents();
  if (next) {
    setTimeout(() => toggleRow(next.id), 100);
  }
}

// ==========================================================================
// Filters
// ==========================================================================
function applyFilters() {
  const fee = document.getElementById('feeFilter').value;
  const grade = document.getElementById('gradeFilter').value;
  const status = document.getElementById('statusFilter').value;
  const course = document.getElementById('courseFilter').value.toLowerCase();
  const name = document.getElementById('nameFilter').value.toLowerCase();

  filteredStudents = allStudents.filter(s => {
    const t = getTier(s.fee).tier;
    const curStatus = getStatus(s.id);
    if (fee !== 'all' && t !== fee) return false;
    if (grade !== 'all' && s.grade !== grade) return false;
    if (status !== 'all' && curStatus !== status) return false;
    if (course && !s.courses.join(' ').toLowerCase().includes(course)) return false;
    if (name && !s.name.toLowerCase().includes(name)) return false;
    return true;
  });
}

function populateGradeFilter() {
  const grades = [...new Set(allStudents.map(s => s.grade).filter(Boolean))].sort();
  const sel = document.getElementById('gradeFilter');
  grades.forEach(g => {
    const opt = document.createElement('option');
    opt.value = g; opt.textContent = g;
    sel.appendChild(opt);
  });
}

// ==========================================================================
// Bulk actions
// ==========================================================================
function getSelectedIds() {
  return [...document.querySelectorAll('[data-select]:checked')].map(el => parseInt(el.dataset.select));
}

function exportCsv() {
  const rows = [['ID', '氏名', '学年', 'コース', '月謝', 'Tier', 'Status', 'Note']];
  allStudents.forEach(s => {
    const t = getTier(s.fee).label;
    rows.push([s.id, s.name, s.grade, s.courses.join('; '), s.fee, t, getStatus(s.id), getNote(s.id)]);
  });
  const csv = rows.map(r => r.map(c => `"${String(c || '').replace(/"/g, '""')}"`).join(',')).join('\n');
  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `outreach-${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

function markSelectedSent() {
  const ids = getSelectedIds();
  if (ids.length === 0) { alert('生徒を選択してください'); return; }
  if (!confirm(`${ids.length}名を「送信済み」にマークしますか？`)) return;
  ids.forEach(id => setStatus(id, 'sent'));
  renderStudents();
}

function copyAllMessages() {
  const ids = getSelectedIds();
  if (ids.length === 0) { alert('生徒を選択してください'); return; }
  const messages = ids.map(id => {
    const student = allStudents.find(s => s.id === id);
    if (!student) return '';
    const msg = generateMessage(student);
    return `=== ${student.name} さん ===\n件名: ${msg.subject}\n\n${msg.body.replace(/<[^>]+>/g, '')}\n\n`;
  }).join('\n---\n\n');
  navigator.clipboard.writeText(messages).then(() => alert(`✅ ${ids.length}名分のメッセージをコピーしました`));
}

function clearAllStatus() {
  if (!confirm('全生徒のステータスをリセットします。本当に続行しますか？')) return;
  localStorage.removeItem(STORAGE_STATUS);
  localStorage.removeItem(STORAGE_NOTES);
  renderStudents();
}

// ==========================================================================
// Init
// ==========================================================================
document.addEventListener('DOMContentLoaded', async () => {
  await loadStudents();
  if (allStudents.length > 0) populateGradeFilter();

  // Filter events
  ['feeFilter', 'gradeFilter', 'statusFilter', 'courseFilter', 'nameFilter'].forEach(id => {
    document.getElementById(id).addEventListener('input', renderStudents);
    document.getElementById(id).addEventListener('change', renderStudents);
  });

  // Bulk action events
  document.getElementById('exportCsv').addEventListener('click', exportCsv);
  document.getElementById('markSelectedSent').addEventListener('click', markSelectedSent);
  document.getElementById('copyAllMessages').addEventListener('click', copyAllMessages);
  document.getElementById('clearStatus').addEventListener('click', clearAllStatus);
  document.getElementById('reloadBtn').addEventListener('click', () => loadStudents());

  // Modal events
  document.getElementById('autoLoadBtn').addEventListener('click', async () => {
    const ok = await loadStudents();
    if (ok) document.getElementById('loadModal').classList.remove('show');
  });
  document.getElementById('uploadBtn').addEventListener('click', () => {
    document.getElementById('fileInput').click();
  });
  document.getElementById('fileInput').addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (evt) => {
      try {
        const data = JSON.parse(evt.target.result);
        processData(data);
        populateGradeFilter();
        updateStatus('🟢 ファイル読込完了', 'live');
        document.getElementById('loadModal').classList.remove('show');
      } catch (err) {
        alert('JSON解析エラー: ' + err.message);
      }
    };
    reader.readAsText(file);
  });
});
