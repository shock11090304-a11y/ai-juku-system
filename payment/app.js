// === juku-payment Phase 1 ===
// データは data.json (juku-manager 由来) + localStorage の差分マージで動作

const STATE = {
  data: null,         // data.json 全体
  overrides: null,    // localStorage 上書き分 (payments / emails / payerNames)
  currentMonth: null, // "YYYY-MM"
};

const LS_KEY = 'juku-payment-overrides-v1';
const SET_KEY = 'juku-payment-settings-v1';

const DEFAULT_MAIL_SUBJECT = '【{{juku}}】{{month}}月分 月謝のお振込確認のお願い';
const DEFAULT_MAIL_BODY = `{{student}} 様の保護者様

いつも{{juku}}をご利用いただきありがとうございます。
標記の件、{{month}}月分の月謝につきまして、現時点で当塾でのご入金確認ができておりません。

お振込みがお済みの場合は、本メールと行き違いとなっておりましたら申し訳ございません。

【ご請求内容】
　・対象月　 : {{month}}月分
　・月謝額　 : ¥{{fee}}
　・お支払期限: {{deadline}}

【お支払い方法】

▼銀行振込
{{bank}}

▼カード決済 (即時お支払い)
　{{paymentLink}}

恐れ入りますが、上記期限までにお支払いをお願い申し上げます。
ご不明な点がございましたらお気軽にご連絡ください。

────────────────────
{{juku}}
{{owner}}
{{ownerEmail}}
{{ownerPhone}}
────────────────────`;

const DEFAULT_SETTINGS = {
  jukuName: '◯◯塾',
  ownerName: '塾長',
  ownerEmail: '',
  ownerPhone: '',
  bankName: '楽天銀行',
  branchName: '',
  accountType: '普通',
  accountNumber: '',
  accountHolder: '',
  deadlineDay: 25,
  dunningTone: 'normal',
  mailSubject: DEFAULT_MAIL_SUBJECT,
  mailBody: DEFAULT_MAIL_BODY,
  stripePaymentLink: '',         // 共通 Stripe Payment Links URL
  stripeLinksByFee: {},          // 金額別: { '7500': 'url', '15000': 'url' }
};

let SETTINGS = { ...DEFAULT_SETTINGS };
let CHARTS = { revenue: null, rate: null, course: null };

// === Utility ===
const yen = (n) => '¥' + (n || 0).toLocaleString('ja-JP');
const todayMonth = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
};

// === Data Load ===
const DATA_KEY = 'juku-payment-data-v1';

async function loadData() {
  // 1. localStorage キャッシュを最優先で使う
  const cached = localStorage.getItem(DATA_KEY);
  if (cached) {
    try { STATE.data = JSON.parse(cached); }
    catch { STATE.data = null; }
  }
  // 2. キャッシュなし → data.json fetch を試す (ローカル/サブパス用)
  if (!STATE.data) {
    try {
      const res = await fetch('data.json?t=' + Date.now());
      if (res.ok) {
        STATE.data = await res.json();
        localStorage.setItem(DATA_KEY, JSON.stringify(STATE.data));
      } else { throw new Error('not found'); }
    } catch (err) {
      // 3. 初回・公開デプロイ → 空データ + 案内表示
      STATE.data = { students: [], courses: [], payments: {}, nextStudentId: 1, nextCourseId: 1 };
      window._needsImport = true;
    }
  }
  STATE.overrides = JSON.parse(localStorage.getItem(LS_KEY) || '{"payments":{},"emails":{},"payerNames":{},"mailSent":{}}');
  if (!STATE.overrides.payments) STATE.overrides.payments = {};
  if (!STATE.overrides.emails) STATE.overrides.emails = {};
  if (!STATE.overrides.payerNames) STATE.overrides.payerNames = {};
  if (!STATE.overrides.mailSent) STATE.overrides.mailSent = {};
  if (!STATE.overrides.status) STATE.overrides.status = {};
}

function getStatus(student) {
  return STATE.overrides.status?.[student.id] ?? student.status;
}
function setStatus(studentId, status) {
  STATE.overrides.status[studentId] = status;
  saveOverrides();
}

function uniqueGrades() {
  const set = new Set();
  STATE.data.students.forEach(s => { if (s.grade) set.add(s.grade); });
  return [...set].sort();
}
function uniqueCourses() {
  const set = new Set();
  // courses マスタ
  (STATE.data.courses || []).forEach(c => { if (c.name) set.add(c.name); });
  // 個別生徒の courses も拾う (マスタにないコース対策)
  STATE.data.students.forEach(s => (s.courses || []).forEach(c => { if (c) set.add(c); }));
  return [...set].sort();
}

function populateSelect(selectId, values, leadingPlaceholder) {
  const sel = document.getElementById(selectId);
  if (!sel) return;
  const cur = sel.value;
  sel.innerHTML = `<option value="">${leadingPlaceholder}</option>` +
    values.map(v => `<option value="${escapeHtml(v)}">${escapeHtml(v)}</option>`).join('');
  if (values.includes(cur)) sel.value = cur;
}
function populateAllFilters() {
  const grades = uniqueGrades();
  const courses = uniqueCourses();
  populateSelect('gradeFilter', grades, '学年: 全て');
  populateSelect('courseFilter', courses, 'コース: 全て');
  populateSelect('unpaidGradeFilter', grades, '学年: 全て');
  populateSelect('unpaidCourseFilter', courses, 'コース: 全て');
  populateSelect('invoiceGradeFilter', grades, '学年: 全て');
  populateSelect('invoiceCourseFilter', courses, 'コース: 全て');
  populateSelect('enrollGradeFilter', grades, '学年: 全て');
  populateSelect('enrollCourseFilter', courses, 'コース: 全て');
}

function loadSettings() {
  const saved = localStorage.getItem(SET_KEY);
  if (saved) {
    try { SETTINGS = { ...DEFAULT_SETTINGS, ...JSON.parse(saved) }; }
    catch { SETTINGS = { ...DEFAULT_SETTINGS }; }
  }
}
function saveSettings() {
  localStorage.setItem(SET_KEY, JSON.stringify(SETTINGS));
}

function getMailSent(month, studentId) {
  return STATE.overrides.mailSent?.[month]?.[studentId] || null;
}
function setMailSent(month, studentId, isoDate) {
  if (!STATE.overrides.mailSent[month]) STATE.overrides.mailSent[month] = {};
  STATE.overrides.mailSent[month][studentId] = isoDate;
  saveOverrides();
}

function saveOverrides() {
  localStorage.setItem(LS_KEY, JSON.stringify(STATE.overrides));
}

// === Merged accessors ===
function getPayment(month, studentId) {
  // override 優先 → なければ data.json
  const ov = STATE.overrides.payments?.[month]?.[studentId];
  if (ov !== undefined) return ov;
  const base = STATE.data.payments?.[month]?.[studentId];
  return base || null;
}

function setPayment(month, studentId, paid, date = '', note = '', amount = null) {
  if (!STATE.overrides.payments[month]) STATE.overrides.payments[month] = {};
  STATE.overrides.payments[month][studentId] = { paid, date, note, amount };
  saveOverrides();
}

function getEmail(studentId) {
  return STATE.overrides.emails?.[studentId] ?? STATE.data.students.find(s => s.id === studentId)?.email ?? '';
}
function setEmail(studentId, email) {
  STATE.overrides.emails[studentId] = email;
  saveOverrides();
}

function getPayerName(studentId) {
  return STATE.overrides.payerNames?.[studentId] ?? '';
}
function setPayerName(studentId, name) {
  STATE.overrides.payerNames[studentId] = name;
  saveOverrides();
}

function activeStudents() {
  return STATE.data.students.filter(s => getStatus(s) === '通塾');
}

function statusSelectClass(status) {
  if (status === '通塾') return 'status-tushuku';
  if (status === '休塾') return 'status-kyusyuku';
  if (status === '退塾') return 'status-taisyuku';
  return '';
}

// === Stats ===
function renderStats() {
  const month = STATE.currentMonth;
  const active = activeStudents();
  let paidCount = 0, paidAmount = 0, unpaidCount = 0, unpaidAmount = 0;
  active.forEach(s => {
    const pay = getPayment(month, s.id);
    if (pay && pay.paid) {
      paidCount++; paidAmount += s.fee || 0;
    } else {
      unpaidCount++; unpaidAmount += s.fee || 0;
    }
  });
  const rate = active.length ? Math.round(paidCount / active.length * 100) : 0;
  document.getElementById('statTotal').textContent = active.length;
  document.getElementById('statPaid').textContent = paidCount;
  document.getElementById('statPaidAmount').textContent = yen(paidAmount);
  document.getElementById('statUnpaid').textContent = unpaidCount;
  document.getElementById('statUnpaidAmount').textContent = yen(unpaidAmount);
  document.getElementById('statRate').textContent = rate;
  document.getElementById('statRateBar').style.width = rate + '%';
}

// === Render Helpers ===
function coursesTags(courses) {
  if (!courses || !courses.length) return '<span style="color:var(--text-muted)">—</span>';
  return courses.map(c => `<span class="course-tag">${escapeHtml(c)}</span>`).join('');
}

function escapeHtml(s) {
  return String(s ?? '').replace(/[&<>"']/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m]));
}

function statusTag(status) {
  if (status === '通塾') return '<span class="status-tag status-active">通塾</span>';
  if (status === '休塾') return '<span class="status-tag status-pause">休塾</span>';
  if (status === '退塾') return '<span class="status-tag status-quit">退塾</span>';
  return `<span class="status-tag">${escapeHtml(status || '—')}</span>`;
}

function statusSelect(student) {
  const cur = getStatus(student);
  return `<select class="status-select ${statusSelectClass(cur)}" data-action="status">
    ${['通塾','休塾','退塾'].map(s => `<option value="${s}" ${s===cur?'selected':''}>${s}</option>`).join('')}
  </select>`;
}

// === Unpaid Tab ===
function renderUnpaid() {
  const month = STATE.currentMonth;
  document.getElementById('unpaidMonthTag').textContent = month;
  const tbody = document.getElementById('unpaidTbody');
  const grade = document.getElementById('unpaidGradeFilter')?.value || '';
  const course = document.getElementById('unpaidCourseFilter')?.value || '';
  let unpaid = activeStudents().filter(s => {
    const pay = getPayment(month, s.id);
    return !pay || !pay.paid;
  });
  if (grade) unpaid = unpaid.filter(s => s.grade === grade);
  if (course) unpaid = unpaid.filter(s => (s.courses || []).includes(course));
  document.getElementById('unpaidCountTag').textContent = `${unpaid.length}名`;

  if (!unpaid.length) {
    tbody.innerHTML = `<tr><td colspan="7" class="empty">🎉 ${month} の未払い者はいません</td></tr>`;
    return;
  }

  tbody.innerHTML = unpaid.map(s => {
    const sent = getMailSent(month, s.id);
    const email = getEmail(s.id);
    const status = sent
      ? `<span class="mail-status mail-sent">✓ ${sent} 送信済</span>`
      : email
        ? `<span class="mail-status mail-pending">未送信</span>`
        : `<span class="mail-status">メール未登録</span>`;
    return `
    <tr data-student-id="${s.id}">
      <td class="id-cell">#${s.id}</td>
      <td class="name-cell">${escapeHtml(s.name)}</td>
      <td>${escapeHtml(s.grade || '—')}</td>
      <td class="ta-r fee-cell">${yen(s.fee)}</td>
      <td><input type="text" class="email-input" data-action="email" placeholder="メール未登録" value="${escapeHtml(email)}"></td>
      <td class="ta-c">${status}</td>
      <td class="ta-c">
        <div class="mail-actions">
          <button class="icon-btn" data-action="mail-preview" title="メール内容を確認">📧 確認</button>
          <button class="icon-btn ${sent ? 'icon-btn-success' : ''}" data-action="mail-send" title="メーラーで開く" ${email ? '' : 'disabled'}>${sent ? '✓ 送信' : '➜ 送信'}</button>
          <button class="pay-toggle" data-action="toggle" title="入金済にする">○</button>
        </div>
      </td>
    </tr>`;
  }).join('');

  tbody.onclick = (e) => {
    const btn = e.target.closest('[data-action]');
    if (!btn) return;
    const tr = btn.closest('tr');
    const id = parseInt(tr.dataset.studentId, 10);
    const a = btn.dataset.action;
    if (a === 'toggle') {
      setPayment(month, id, true, new Date().toISOString().slice(0, 10), '手動チェック', null);
      refresh();
    } else if (a === 'mail-preview') {
      openMailPreview(id);
    } else if (a === 'mail-send') {
      sendMailTo(id);
      renderUnpaid();
    }
  };
  tbody.oninput = (e) => {
    const t = e.target;
    const tr = t.closest('tr'); if (!tr) return;
    const id = parseInt(tr.dataset.studentId, 10);
    if (t.dataset.action === 'email') setEmail(id, t.value.trim());
  };
}

// === All Students Tab ===
function renderAll() {
  const tbody = document.getElementById('allTbody');
  const search = document.getElementById('searchInput').value.toLowerCase();
  const statusFilter = document.getElementById('statusFilter').value;
  const gradeFilter = document.getElementById('gradeFilter')?.value || '';
  const courseFilter = document.getElementById('courseFilter')?.value || '';
  const month = STATE.currentMonth;

  let students = STATE.data.students.slice();
  if (statusFilter) students = students.filter(s => getStatus(s) === statusFilter);
  if (gradeFilter) students = students.filter(s => s.grade === gradeFilter);
  if (courseFilter) students = students.filter(s => (s.courses || []).includes(courseFilter));
  if (search) students = students.filter(s => (s.name || '').toLowerCase().includes(search));

  document.getElementById('allCountTag').textContent = `${students.length}名 / ${STATE.data.students.length}名中`;

  if (!students.length) {
    tbody.innerHTML = `<tr><td colspan="9" class="empty">該当する生徒はいません</td></tr>`;
    return;
  }

  tbody.innerHTML = students.map(s => {
    const pay = getPayment(month, s.id);
    const paid = pay && pay.paid;
    return `
    <tr data-student-id="${s.id}">
      <td class="id-cell">#${s.id}</td>
      <td class="name-cell">${escapeHtml(s.name)}</td>
      <td>${escapeHtml(s.grade || '—')}</td>
      <td>${coursesTags(s.courses)}</td>
      <td class="ta-r fee-cell">${yen(s.fee)}</td>
      <td><input type="text" class="email-input" data-action="email" placeholder="未登録" value="${escapeHtml(getEmail(s.id))}"></td>
      <td><input type="text" class="payer-input" data-action="payer" placeholder="—" value="${escapeHtml(getPayerName(s.id))}"></td>
      <td>${statusSelect(s)}</td>
      <td class="ta-c">
        <button class="pay-toggle ${paid ? 'paid' : ''}" data-action="toggle" title="${paid ? '入金済' : '未払い'}">${paid ? '✓' : '○'}</button>
      </td>
    </tr>`;
  }).join('');

  tbody.onclick = (e) => {
    const btn = e.target.closest('[data-action="toggle"]');
    if (!btn) return;
    const tr = btn.closest('tr');
    const id = parseInt(tr.dataset.studentId, 10);
    const pay = getPayment(month, id);
    const newPaid = !(pay && pay.paid);
    setPayment(month, id, newPaid, newPaid ? new Date().toISOString().slice(0, 10) : '', newPaid ? '手動チェック' : '', null);
    refresh();
  };
  tbody.onchange = (e) => {
    const sel = e.target.closest('select[data-action="status"]');
    if (!sel) return;
    const tr = sel.closest('tr');
    const id = parseInt(tr.dataset.studentId, 10);
    setStatus(id, sel.value);
    sel.className = `status-select ${statusSelectClass(sel.value)}`;
    renderStats(); // active count を再計算
    document.getElementById('allCountTag').textContent =
      `${tbody.querySelectorAll('tr').length}名 / ${STATE.data.students.length}名中`;
  };
  tbody.oninput = (e) => {
    const t = e.target;
    const tr = t.closest('tr'); if (!tr) return;
    const id = parseInt(tr.dataset.studentId, 10);
    if (t.dataset.action === 'email') setEmail(id, t.value.trim());
    else if (t.dataset.action === 'payer') setPayerName(id, t.value.trim());
  };
}

// === History Tab (直近6ヶ月マトリクス) ===
function renderHistory() {
  const months = [];
  const cur = new Date(STATE.currentMonth + '-01');
  for (let i = 5; i >= 0; i--) {
    const d = new Date(cur.getFullYear(), cur.getMonth() - i, 1);
    months.push(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`);
  }

  const head = document.getElementById('historyHead');
  head.innerHTML = '<th>ID</th><th>氏名</th>' + months.map(m => `<th class="ta-c">${m}</th>`).join('');

  const tbody = document.getElementById('historyTbody');
  tbody.innerHTML = activeStudents().map(s => {
    const cells = months.map(m => {
      const pay = getPayment(m, s.id);
      if (pay && pay.paid) return '<td class="ta-c"><span class="history-cell paid">✓</span></td>';
      return '<td class="ta-c"><span class="history-cell unpaid">×</span></td>';
    }).join('');
    return `<tr>
      <td class="id-cell">#${s.id}</td>
      <td class="name-cell">${escapeHtml(s.name)}</td>
      ${cells}
    </tr>`;
  }).join('');
}

// === Tab switching ===
function switchTab(name) {
  document.querySelectorAll('.tab').forEach(t => {
    t.classList.toggle('tab-active', t.dataset.tab === name);
  });
  document.querySelectorAll('[data-panel]').forEach(p => {
    p.classList.toggle('hidden', p.dataset.panel !== name);
  });
  if (name === 'unpaid') renderUnpaid();
  else if (name === 'all') renderAll();
  else if (name === 'history') renderHistory();
  else if (name === 'dashboard') renderDashboard();
  else if (name === 'invoice') renderInvoiceTab();
  else if (name === 'enrollment') renderEnrollment();
}

// === Refresh all visible ===
function refresh() {
  renderStats();
  const active = document.querySelector('.tab-active')?.dataset.tab || 'dashboard';
  if (active === 'unpaid') renderUnpaid();
  else if (active === 'all') renderAll();
  else if (active === 'history') renderHistory();
  else if (active === 'dashboard') renderDashboard();
  else if (active === 'invoice') renderInvoiceTab();
  else if (active === 'enrollment') renderEnrollment();
}

// === Phase 2: CSV Import ===
const NOISE_PATTERNS = [
  /ラクテンショウケン/,
  /カ[−ー\-]ド出金/,
  /口座振替/,
  /ATM/i,
  /テレボ/,
  /利息/,
  /スイ[−ー\-]プ/,
  /手数料/,
  /振込手数/,
];
const DAKUTEN = { 'カ':'ガ','キ':'ギ','ク':'グ','ケ':'ゲ','コ':'ゴ',
                  'サ':'ザ','シ':'ジ','ス':'ズ','セ':'ゼ','ソ':'ゾ',
                  'タ':'ダ','チ':'ヂ','ツ':'ヅ','テ':'デ','ト':'ド',
                  'ハ':'バ','ヒ':'ビ','フ':'ブ','ヘ':'ベ','ホ':'ボ',
                  'ウ':'ヴ' };
const HANDAKUTEN = { 'ハ':'パ','ヒ':'ピ','フ':'プ','ヘ':'ペ','ホ':'ポ' };

const IMPORT = { rows: [], candidates: [], filterTab: 'pending' };

function normalizeName(raw) {
  if (!raw) return '';
  let s = String(raw)
    .replace(/(.)[゛ﾞ]/g, (m, c) => DAKUTEN[c] || c)
    .replace(/(.)[゜ﾟ]/g, (m, c) => HANDAKUTEN[c] || c)
    .replace(/[ァ-ヶ]/g, m => String.fromCharCode(m.charCodeAt(0) - 0x60))
    .replace(/[\s　]+/g, '')
    .replace(/(英語(塾代|代|月謝)?|月謝|塾代)$/, '')
    .toLowerCase();
  return s;
}

function isNoise(content) {
  return NOISE_PATTERNS.some(p => p.test(content));
}

function lcs(a, b) {
  let best = '';
  for (let i = 0; i < a.length; i++) {
    for (let j = i + 1; j <= a.length && (j - i) <= 8; j++) {
      const sub = a.slice(i, j);
      if (sub.length > best.length && b.includes(sub)) best = sub;
    }
  }
  return best;
}

function matchPayer(payerRaw) {
  const normPayer = normalizeName(payerRaw);
  if (!normPayer) return [];

  // 1. 学習済 payerNames で完全一致
  for (const [sid, payer] of Object.entries(STATE.overrides.payerNames || {})) {
    if (payer && normalizeName(payer) === normPayer) {
      const s = STATE.data.students.find(x => x.id === parseInt(sid, 10));
      if (s) return [{ studentId: s.id, name: s.name, score: 100, confidence: 'learned' }];
    }
  }

  // 2. 全通塾生でスコア計算
  const cands = STATE.data.students
    .filter(s => s.status === '通塾')
    .map(s => {
      const norm = normalizeName(s.name);
      if (!norm) return null;
      let score = 0;
      if (norm === normPayer) score = 100;
      else if (norm.includes(normPayer) || normPayer.includes(norm)) score = 85;
      else {
        const common = lcs(norm, normPayer);
        if (common.length >= 2) score = Math.min(70, common.length * 18);
      }
      return score > 0 ? { studentId: s.id, name: s.name, score } : null;
    })
    .filter(Boolean)
    .sort((a, b) => b.score - a.score)
    .slice(0, 5);

  return cands.map(c => ({
    ...c,
    confidence: c.score >= 90 ? 'high' : c.score >= 65 ? 'mid' : 'low',
  }));
}

function parseCSVText(text) {
  const lines = text.split(/\r?\n/).filter(l => l.trim());
  const out = [];
  for (let i = 1; i < lines.length; i++) {
    const cols = lines[i].split(',');
    if (cols.length < 4) continue;
    const date = cols[0].trim();
    const amount = parseInt(cols[1].trim(), 10);
    const balance = parseInt(cols[2].trim(), 10);
    const content = cols.slice(3).join(',').trim();
    if (isNaN(amount)) continue;
    out.push({ date, amount, balance, content });
  }
  return out;
}

function csvDateToMonth(d) {
  // YYYYMMDD -> YYYY-MM
  if (!d || d.length < 6) return STATE.currentMonth;
  return `${d.slice(0, 4)}-${d.slice(4, 6)}`;
}
function csvDateToISO(d) {
  if (!d || d.length < 8) return '';
  return `${d.slice(0, 4)}-${d.slice(4, 6)}-${d.slice(6, 8)}`;
}

async function decodeFile(file) {
  const buf = await file.arrayBuffer();
  // 楽天銀行は Shift_JIS。失敗したら UTF-8 を試す
  try {
    const dec = new TextDecoder('shift_jis', { fatal: false });
    const text = dec.decode(buf);
    if (text.includes('取引日') || text.includes('入出金')) return text;
  } catch (e) { /* fallthrough */ }
  return new TextDecoder('utf-8').decode(buf);
}

function processImport(rows) {
  IMPORT.rows = rows;
  const incoming = rows.filter(r => r.amount > 0);

  IMPORT.candidates = incoming.map((r, i) => {
    const ignored = isNoise(r.content);
    const matches = ignored ? [] : matchPayer(r.content);
    const best = matches[0];
    return {
      idx: i,
      date: r.date,
      month: csvDateToMonth(r.date),
      iso: csvDateToISO(r.date),
      amount: r.amount,
      payer: r.content,
      matches,
      selectedStudentId: best && (best.confidence === 'learned' || best.confidence === 'high') ? best.studentId : null,
      decided: !!(best && (best.confidence === 'learned' || best.confidence === 'high')),
      ignored,
    };
  });

  document.getElementById('sumRows').textContent = rows.length;
  document.getElementById('sumIncoming').textContent = incoming.length;
  document.getElementById('sumCandidates').textContent = IMPORT.candidates.filter(c => !c.ignored).length;
  document.getElementById('sumMatched').textContent = IMPORT.candidates.filter(c => c.decided && !c.ignored).length;
  document.getElementById('sumPending').textContent = IMPORT.candidates.filter(c => !c.decided && !c.ignored).length;
  document.getElementById('importResults').classList.remove('hidden');
  document.getElementById('applyImportBtn').disabled = false;
  renderMatchList();
}

function renderMatchList() {
  const tab = IMPORT.filterTab;
  const list = document.getElementById('matchList');
  let items = IMPORT.candidates;
  if (tab === 'pending') items = items.filter(c => !c.decided && !c.ignored);
  else if (tab === 'matched') items = items.filter(c => c.decided && !c.ignored);
  else if (tab === 'ignored') items = items.filter(c => c.ignored);

  if (!items.length) {
    list.innerHTML = `<div class="empty" style="padding:2rem;text-align:center;color:var(--text-muted)">該当なし</div>`;
    return;
  }

  list.innerHTML = items.map(c => {
    const cls = c.ignored ? 'match-ignored' : c.decided ? 'match-matched' : 'match-pending';
    const options = [
      `<option value="">${c.ignored ? '— 除外（ノイズ）—' : '生徒を選択…'}</option>`,
      ...c.matches.map(m => {
        const conf = m.confidence === 'learned' ? '学習済' : m.confidence === 'high' ? '高' : m.confidence === 'mid' ? '中' : '低';
        return `<option value="${m.studentId}" ${c.selectedStudentId === m.studentId ? 'selected' : ''}>#${m.studentId} ${escapeHtml(m.name)} (${conf}: ${m.score})</option>`;
      }),
      // 自由選択用に全生徒を末尾に
      `<optgroup label="── 手動選択 ──">`,
      ...activeStudents().map(s => `<option value="${s.id}" ${c.selectedStudentId === s.id ? 'selected' : ''}>#${s.id} ${escapeHtml(s.name)} ${yen(s.fee)}</option>`),
      `</optgroup>`
    ].join('');

    return `
      <div class="match-row ${cls}" data-idx="${c.idx}">
        <div class="match-date">${c.iso}</div>
        <div class="match-payer">${escapeHtml(c.payer)}</div>
        <div class="match-amount">${yen(c.amount)}</div>
        <div>
          ${c.ignored
            ? '<span style="color:var(--text-muted);font-size:0.82rem">— ノイズとして除外 —</span>'
            : `<select class="match-student-select" data-action="select">${options}</select>`
          }
        </div>
        <div class="match-actions">
          ${c.ignored
            ? `<button class="match-btn" data-action="unignore" title="除外を解除">↺ 復活</button>`
            : `<button class="match-btn" data-action="confirm">${c.decided ? '✓ 確定済' : '✓ 確定'}</button>
               <button class="match-btn match-btn-skip" data-action="ignore">— 除外</button>`
          }
        </div>
      </div>
    `;
  }).join('');

  list.onchange = (e) => {
    const sel = e.target.closest('select');
    if (!sel) return;
    const row = e.target.closest('.match-row');
    const idx = parseInt(row.dataset.idx, 10);
    const c = IMPORT.candidates.find(x => x.idx === idx);
    c.selectedStudentId = sel.value ? parseInt(sel.value, 10) : null;
    c.decided = !!c.selectedStudentId;
    updateImportSummary();
    row.className = `match-row ${c.decided ? 'match-matched' : 'match-pending'}`;
  };
  list.onclick = (e) => {
    const btn = e.target.closest('[data-action]');
    if (!btn) return;
    const row = btn.closest('.match-row');
    const idx = parseInt(row.dataset.idx, 10);
    const c = IMPORT.candidates.find(x => x.idx === idx);
    const a = btn.dataset.action;
    if (a === 'confirm') {
      if (!c.selectedStudentId) { alert('生徒を選択してください'); return; }
      c.decided = true;
    } else if (a === 'ignore') {
      c.ignored = true; c.decided = false; c.selectedStudentId = null;
    } else if (a === 'unignore') {
      c.ignored = false;
      const matches = matchPayer(c.payer);
      c.matches = matches;
      const best = matches[0];
      if (best && (best.confidence === 'learned' || best.confidence === 'high')) {
        c.selectedStudentId = best.studentId; c.decided = true;
      }
    }
    updateImportSummary();
    renderMatchList();
  };
}

function updateImportSummary() {
  document.getElementById('sumMatched').textContent = IMPORT.candidates.filter(c => c.decided && !c.ignored).length;
  document.getElementById('sumPending').textContent = IMPORT.candidates.filter(c => !c.decided && !c.ignored).length;
}

function applyImport() {
  const decided = IMPORT.candidates.filter(c => c.decided && c.selectedStudentId);
  if (!decided.length) { alert('確定済の入金がありません'); return; }
  const msg = `${decided.length}件 を入金反映します。\n\n` +
    `内訳: \n  ・自動マッチ ${decided.filter(c => c.matches[0]?.confidence === 'high' || c.matches[0]?.confidence === 'learned').length}件\n  ・手動マッチ ${decided.filter(c => !(c.matches[0]?.confidence === 'high' || c.matches[0]?.confidence === 'learned')).length}件\n\n振込人名は次回CSVのために学習保存されます。続行しますか？`;
  if (!confirm(msg)) return;

  let updated = 0;
  decided.forEach(c => {
    setPayment(c.month, c.selectedStudentId, true, c.iso, `楽天銀行CSV: ${c.payer}`, c.amount);
    setPayerName(c.selectedStudentId, c.payer);
    updated++;
  });
  alert(`✅ ${updated}件 を入金反映しました\n振込人名 ${updated}件 を学習保存しました`);
  document.getElementById('importResults').classList.add('hidden');
  IMPORT.candidates = []; IMPORT.rows = [];
  switchTab('unpaid');
  refresh();
}

// ファイル受け取り
function setupImportUI() {
  const area = document.getElementById('uploadArea');
  const input = document.getElementById('csvFile');
  area.addEventListener('click', () => input.click());
  area.addEventListener('dragover', (e) => { e.preventDefault(); area.classList.add('dragover'); });
  area.addEventListener('dragleave', () => area.classList.remove('dragover'));
  area.addEventListener('drop', async (e) => {
    e.preventDefault(); area.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file) await handleFile(file);
  });
  input.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (file) await handleFile(file);
  });
  document.querySelectorAll('.match-tab').forEach(t => {
    t.addEventListener('click', () => {
      IMPORT.filterTab = t.dataset.matchTab;
      document.querySelectorAll('.match-tab').forEach(x => x.classList.toggle('match-tab-active', x === t));
      renderMatchList();
    });
  });
  document.getElementById('applyImportBtn').addEventListener('click', applyImport);
  document.getElementById('resetImportBtn').addEventListener('click', () => {
    IMPORT.candidates = []; IMPORT.rows = [];
    document.getElementById('importResults').classList.add('hidden');
    document.getElementById('csvFile').value = '';
  });
}

async function handleFile(file) {
  try {
    const text = await decodeFile(file);
    const rows = parseCSVText(text);
    if (!rows.length) { alert('CSVに有効な行が見つかりませんでした'); return; }
    processImport(rows);
  } catch (err) {
    console.error(err);
    alert('CSV読込エラー: ' + err.message);
  }
}

// === Phase 3: Mail (mailto + template + history) ===

function bankInfoText() {
  const s = SETTINGS;
  return [
    s.bankName || '楽天銀行',
    s.branchName ? ` ${s.branchName}` : '',
    `　${s.accountType || '普通'} ${s.accountNumber || '—'}`,
    `　名義: ${s.accountHolder || '—'}`
  ].join('');
}

function renderTemplate(tpl, vars) {
  return String(tpl || '').replace(/\{\{(\w+)\}\}/g, (m, k) => vars[k] ?? m);
}

function deadlineForMonth(month) {
  const d = parseInt(SETTINGS.deadlineDay, 10) || 25;
  return `${month}-${String(d).padStart(2, '0')}`;
}

function paymentLinkFor(student) {
  const fee = String(student.fee || '');
  return SETTINGS.stripeLinksByFee?.[fee] || SETTINGS.stripePaymentLink || '(未設定)';
}

function buildMailFor(studentId) {
  const s = STATE.data.students.find(x => x.id === studentId);
  if (!s) return null;
  const month = STATE.currentMonth;
  const vars = {
    student: s.name,
    juku: SETTINGS.jukuName,
    owner: SETTINGS.ownerName,
    ownerEmail: SETTINGS.ownerEmail,
    ownerPhone: SETTINGS.ownerPhone,
    month: month,
    fee: (s.fee || 0).toLocaleString('ja-JP'),
    deadline: deadlineForMonth(month),
    bank: bankInfoText().split('　').join('\n'),
    paymentLink: paymentLinkFor(s),
  };
  return {
    student: s,
    to: getEmail(studentId),
    subject: renderTemplate(SETTINGS.mailSubject, vars),
    body: renderTemplate(SETTINGS.mailBody, vars),
  };
}

function mailtoUrl(to, subject, body) {
  const params = new URLSearchParams();
  if (subject) params.set('subject', subject);
  if (body) params.set('body', body);
  const q = params.toString().replace(/\+/g, '%20');
  return `mailto:${encodeURIComponent(to || '')}?${q}`;
}

// Safari/Firefox の mailto は URL ~2000文字で壊れる
const MAILTO_SAFE_LIMIT = 1800;
function mailtoSafetyCheck(to, subject, body) {
  const url = mailtoUrl(to, subject, body);
  if (url.length > MAILTO_SAFE_LIMIT) {
    const ok = confirm(
      `⚠ メール本文が長すぎます (${url.length}文字)。\n` +
      `一部メーラーで本文が切れる可能性があります。\n\n` +
      `OK = それでも送信を試みる\n` +
      `キャンセル = クリップボードに本文をコピーして手動で貼り付け`
    );
    if (!ok) {
      copyToClipboard(`To: ${to}\n件名: ${subject}\n\n${body}`);
      alert('📋 件名+本文をクリップボードにコピーしました。Gmail等の新規メールに貼り付けてください。');
      return false;
    }
  }
  return true;
}

function openMailPreview(studentId) {
  const m = buildMailFor(studentId);
  if (!m) return;
  document.getElementById('mailPrevTo').value = m.to || '(メアド未登録)';
  document.getElementById('mailPrevSubject').value = m.subject;
  document.getElementById('mailPrevBody').value = m.body;
  document.getElementById('mailSendBtn').dataset.studentId = studentId;
  document.getElementById('mailCopyBtn').dataset.studentId = studentId;
  showModal('mailPreviewModal');
}

function sendMailTo(studentId) {
  const m = buildMailFor(studentId);
  if (!m) return;
  if (!m.to) { alert('メールアドレスが未登録です'); return; }
  if (!mailtoSafetyCheck(m.to, m.subject, m.body)) return;
  window.open(mailtoUrl(m.to, m.subject, m.body), '_blank');
  setMailSent(STATE.currentMonth, studentId, new Date().toISOString().slice(0, 10));
}

function copyToClipboard(text) {
  navigator.clipboard.writeText(text).catch(() => {
    const ta = document.createElement('textarea');
    ta.value = text; document.body.appendChild(ta); ta.select();
    document.execCommand('copy'); ta.remove();
  });
}

function bulkUnpaidWithEmail() {
  const month = STATE.currentMonth;
  return activeStudents().filter(s => {
    const pay = getPayment(month, s.id);
    if (pay && pay.paid) return false;
    return !!getEmail(s.id);
  });
}

function openBulkMailModal() {
  const targets = bulkUnpaidWithEmail();
  const month = STATE.currentMonth;
  const noEmail = activeStudents().filter(s => {
    const pay = getPayment(month, s.id);
    return (!pay || !pay.paid) && !getEmail(s.id);
  }).length;
  document.getElementById('bulkMailSummary').innerHTML =
    `<strong>${month}</strong> の未払い者:<br>` +
    `　・メアド登録済: <strong style="color:var(--success)">${targets.length}名</strong> → 送信対象<br>` +
    `　・メアド未登録: <strong style="color:var(--warning)">${noEmail}名</strong> → 全生徒タブで登録してください`;
  showModal('bulkMailModal');
}

function bulkMailSequential() {
  const targets = bulkUnpaidWithEmail();
  if (!targets.length) { alert('送信対象がありません'); return; }
  hideModal('bulkMailModal');
  if (!confirm(`${targets.length}名のメーラーを順次開きます。\nブラウザのポップアップブロックを解除してください。続行しますか？`)) return;
  const month = STATE.currentMonth;
  let i = 0;
  const next = () => {
    if (i >= targets.length) { alert(`✅ ${targets.length}名分のメーラーを開きました`); refresh(); return; }
    const s = targets[i];
    const m = buildMailFor(s.id);
    window.open(mailtoUrl(m.to, m.subject, m.body), '_blank');
    setMailSent(month, s.id, new Date().toISOString().slice(0, 10));
    i++;
    setTimeout(next, 800);
  };
  next();
}

function bulkMailBccCopy() {
  const targets = bulkUnpaidWithEmail();
  if (!targets.length) { alert('送信対象がありません'); return; }
  const bcc = targets.map(s => getEmail(s.id)).join(', ');
  // 共通テンプレート (生徒名なし)
  const vars = {
    student: '保護者各位',
    juku: SETTINGS.jukuName,
    owner: SETTINGS.ownerName,
    ownerEmail: SETTINGS.ownerEmail,
    ownerPhone: SETTINGS.ownerPhone,
    month: STATE.currentMonth,
    fee: '(各人別)',
    deadline: deadlineForMonth(STATE.currentMonth),
    bank: bankInfoText().split('　').join('\n'),
  };
  const subject = renderTemplate(SETTINGS.mailSubject, vars);
  const body = renderTemplate(SETTINGS.mailBody, vars);
  const text = `BCC: ${bcc}\n\n件名: ${subject}\n\n${body}`;
  copyToClipboard(text);
  alert(`📋 ${targets.length}名分のBCC・件名・本文をクリップボードにコピーしました\n\nGmail等の新規メール作成画面に貼り付けてください。`);
  hideModal('bulkMailModal');
}

// === Phase 4: Invoice PDF ===

function renderInvoiceTab() {
  const month = STATE.currentMonth;
  document.getElementById('invoiceMonthTag').textContent = month;
  const target = document.querySelector('input[name="invoiceTarget"]:checked')?.value || 'all';
  const grade = document.getElementById('invoiceGradeFilter')?.value || '';
  const course = document.getElementById('invoiceCourseFilter')?.value || '';
  let students = activeStudents();
  if (target === 'unpaid') {
    students = students.filter(s => {
      const pay = getPayment(month, s.id);
      return !pay || !pay.paid;
    });
  }
  if (grade) students = students.filter(s => s.grade === grade);
  if (course) students = students.filter(s => (s.courses || []).includes(course));
  const tbody = document.getElementById('invoiceTbody');
  if (!students.length) {
    tbody.innerHTML = `<tr><td colspan="8" class="empty">該当する生徒がいません</td></tr>`;
    return;
  }
  tbody.innerHTML = students.map(s => {
    const pay = getPayment(month, s.id);
    const paid = pay && pay.paid;
    return `
    <tr data-student-id="${s.id}">
      <td class="ta-c"><input type="checkbox" class="invoice-check" ${target === 'select' ? '' : 'checked'} value="${s.id}"></td>
      <td class="id-cell">#${s.id}</td>
      <td class="name-cell">${escapeHtml(s.name)}</td>
      <td>${escapeHtml(s.grade || '—')}</td>
      <td>${coursesTags(s.courses)}</td>
      <td class="ta-r fee-cell">${yen(s.fee)}</td>
      <td class="ta-c">${paid ? '<span class="status-tag status-active">入金済</span>' : '<span class="status-tag status-pause">未入金</span>'}</td>
      <td class="ta-c"><button class="icon-btn" data-invoice-id="${s.id}">📄 PDF</button></td>
    </tr>`;
  }).join('');

  tbody.onclick = (e) => {
    const btn = e.target.closest('[data-invoice-id]');
    if (btn) {
      const id = parseInt(btn.dataset.invoiceId, 10);
      generateInvoicePDF(id, /*download*/ true);
    }
  };
}

function getSelectedInvoiceIds() {
  return [...document.querySelectorAll('.invoice-check:checked')].map(c => parseInt(c.value, 10));
}

function generateInvoicePDF(studentId, download = true, returnDoc = false) {
  const s = STATE.data.students.find(x => x.id === studentId);
  if (!s) return null;
  const month = STATE.currentMonth;
  const { jsPDF } = window.jspdf;
  const doc = new jsPDF({ unit: 'mm', format: 'a4' });
  // 日本語フォント未組込のため、jsPDFのデフォルトフォントだとカナ/漢字は出ないことが多い
  // → autoTable + 既定フォントで対応 (Helvetica)
  // 日本語混在は doc.text で記号化されるリスクがあるが、最低限の英数+記号でレイアウトする
  // 真の日本語対応はNoto SansフォントをBase64で組み込む必要があるが、今回は autoTable を使った構造化レイアウトで読みやすさ確保

  // タイトル
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(22);
  doc.text('INVOICE / Seikyusho', 105, 22, { align: 'center' });
  doc.setFontSize(10);
  doc.setFont('helvetica', 'normal');
  doc.text(`No. ${month}-${String(s.id).padStart(4, '0')}`, 200, 14, { align: 'right' });
  doc.text(`Date: ${new Date().toISOString().slice(0,10)}`, 200, 19, { align: 'right' });

  // 生徒情報 (日本語は ASCII transliteration ではなく そのまま入れる - フォント未対応で文字化けする可能性ありを許容)
  // 代わりに HTML + html2canvas でPDFにする方が確実。autoTableで構造を持たせる
  const rows = [
    ['Student / Seito',  s.name],
    ['Grade / Gakunen',  s.grade || '-'],
    ['Course',           (s.courses || []).join(', ') || '-'],
    ['Period / Tsukiwari',`${month}`],
    ['Due / Kigen',      deadlineForMonth(month)],
    ['Amount / Kingaku', `JPY ${(s.fee || 0).toLocaleString('en-US')}`],
  ];

  doc.autoTable({
    startY: 35,
    head: [[`Bill To`, '']],
    body: rows,
    theme: 'grid',
    styles: { fontSize: 11, cellPadding: 3 },
    headStyles: { fillColor: [99, 102, 241], textColor: 255 },
    columnStyles: { 0: { cellWidth: 60, fontStyle: 'bold' } },
  });

  // 振込先
  const finalY = doc.lastAutoTable.finalY + 10;
  doc.autoTable({
    startY: finalY,
    head: [['Bank Transfer / Furikomi-saki', '']],
    body: [
      ['Bank',     SETTINGS.bankName || 'Rakuten Bank'],
      ['Branch',   SETTINGS.branchName || '-'],
      ['Type',     SETTINGS.accountType || 'Futsu (Ordinary)'],
      ['Number',   SETTINGS.accountNumber || '-'],
      ['Holder',   SETTINGS.accountHolder || '-'],
    ],
    theme: 'grid',
    styles: { fontSize: 11, cellPadding: 3 },
    headStyles: { fillColor: [236, 72, 153], textColor: 255 },
    columnStyles: { 0: { cellWidth: 60, fontStyle: 'bold' } },
  });

  // カード決済 (Stripe Payment Link)
  const stripeUrl = paymentLinkFor(s);
  if (stripeUrl && stripeUrl !== '(未設定)') {
    const finalYC = doc.lastAutoTable.finalY + 8;
    doc.autoTable({
      startY: finalYC,
      head: [['Card Payment / Card-bara', '']],
      body: [
        ['URL', stripeUrl],
        ['Note', 'Click the URL to pay by credit card via Stripe.'],
      ],
      theme: 'grid',
      styles: { fontSize: 9, cellPadding: 3 },
      headStyles: { fillColor: [16, 185, 129], textColor: 255 },
      columnStyles: { 0: { cellWidth: 30, fontStyle: 'bold' }, 1: { cellWidth: 'auto' } },
    });
  }

  // 合計
  const finalY2 = doc.lastAutoTable.finalY + 10;
  doc.setFontSize(14);
  doc.setFont('helvetica', 'bold');
  doc.text(`TOTAL: JPY ${(s.fee || 0).toLocaleString('en-US')}`, 200, finalY2 + 6, { align: 'right' });

  // フッター
  doc.setFontSize(9);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(120);
  doc.text(SETTINGS.jukuName || 'Juku', 14, 285);
  doc.text(SETTINGS.ownerName || '', 14, 290);
  if (SETTINGS.ownerEmail) doc.text(SETTINGS.ownerEmail, 14, 295);
  doc.text(`Page 1 of 1`, 200, 290, { align: 'right' });

  if (returnDoc) return doc;
  if (download) {
    const filename = `invoice_${month}_${s.id}_${(s.name || '').slice(0, 10)}.pdf`;
    doc.save(filename);
  }
  return doc;
}

async function bulkInvoicePDF() {
  const ids = getSelectedInvoiceIds();
  if (!ids.length) { alert('対象を選択してください'); return; }
  if (ids.length > 100 && !confirm(`${ids.length}名分を生成します。時間がかかります。続行しますか？`)) return;

  const zip = new JSZip();
  const month = STATE.currentMonth;
  for (const id of ids) {
    const doc = generateInvoicePDF(id, false, true);
    if (doc) {
      const s = STATE.data.students.find(x => x.id === id);
      const filename = `invoice_${month}_${id}_${(s?.name || '').slice(0, 10)}.pdf`;
      zip.file(filename, doc.output('blob'));
    }
  }
  const blob = await zip.generateAsync({ type: 'blob' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = `invoices_${month}.zip`;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  alert(`✅ ${ids.length}件の請求書PDFを ZIP でダウンロードしました`);
}

function previewInvoicePDF() {
  const ids = getSelectedInvoiceIds();
  const id = ids[0] || activeStudents()[0]?.id;
  if (!id) { alert('対象を選択してください'); return; }
  const doc = generateInvoicePDF(id, false, true);
  const blob = doc.output('blob');
  const url = URL.createObjectURL(blob);
  document.getElementById('invoiceIframe').src = url;
  document.getElementById('invoiceDownloadBtn').dataset.studentId = id;
  showModal('invoicePreviewModal');
}

// === Phase 5: Export / Import ===

function exportAll() {
  const payload = {
    exportedAt: new Date().toISOString(),
    version: '1.0',
    data: STATE.data,
    overrides: STATE.overrides,
    settings: SETTINGS,
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `juku-payment-backup-${new Date().toISOString().slice(0,10)}.json`;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

async function importAll(file) {
  try {
    const text = await file.text();
    const json = JSON.parse(text);

    // 件数プレビュー
    const ov = json.overrides || {};
    const payMonths = Object.keys(ov.payments || {});
    const payCount = payMonths.reduce((n, m) => n + Object.keys(ov.payments[m]).length, 0);
    const pnCount = Object.keys(ov.payerNames || {}).length;
    const stCount = Object.keys(ov.status || {}).length;

    const note = json.note ? `\n📝 ${json.note}\n` : '';
    const summary = `インポート内容:\n` +
      `　・入金記録 (payments): ${payCount}件 (${payMonths.length}ヶ月)\n` +
      `　・振込人名学習 (payerNames): ${pnCount}件\n` +
      `　・ステータス (status): ${stCount}件\n` +
      `　・メール (emails): ${Object.keys(ov.emails || {}).length}件\n${note}\n` +
      `▶ 既存データと**マージ**します (同一キーは新規データで上書き、それ以外は保持)。\n` +
      `\n続行しますか？\n※心配なら先に💾エクスポートでバックアップを取ってから実行してください`;
    if (!confirm(summary)) return;

    // マージ
    if (json.overrides) {
      const merged = {
        payments: { ...STATE.overrides.payments },
        emails: { ...(STATE.overrides.emails || {}), ...(ov.emails || {}) },
        payerNames: { ...(STATE.overrides.payerNames || {}), ...(ov.payerNames || {}) },
        mailSent: { ...(STATE.overrides.mailSent || {}), ...(ov.mailSent || {}) },
        status: { ...(STATE.overrides.status || {}), ...(ov.status || {}) },
      };
      for (const m of Object.keys(ov.payments || {})) {
        merged.payments[m] = { ...(merged.payments[m] || {}), ...ov.payments[m] };
      }
      STATE.overrides = merged;
      saveOverrides();
    }
    // 生徒データ本体もインポート対象 (公開URL初回ロード用)
    if (json.data && json.data.students) {
      STATE.data = json.data;
      localStorage.setItem(DATA_KEY, JSON.stringify(STATE.data));
      window._needsImport = false;
      const banner = document.getElementById('initial-import-banner');
      if (banner) banner.remove();
    }
    if (json.settings && Object.keys(json.settings).length) {
      SETTINGS = { ...DEFAULT_SETTINGS, ...SETTINGS, ...json.settings };
      saveSettings();
    }
    populateAllFilters();
    alert(`✅ インポート完了\n　・入金記録 +${payCount}件\n　・振込人名学習 +${pnCount}件`);
    refresh();
  } catch (err) {
    alert('読込失敗: ' + err.message);
  }
}

// === Phase 7: Enrollment audit ===

function lastNMonths(curMonth, n) {
  const cur = new Date(curMonth + '-01');
  return Array.from({ length: n }, (_, i) => {
    const d = new Date(cur.getFullYear(), cur.getMonth() - (n - 1 - i), 1);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
  });
}

function categorizeStudent(student, monthsWindow) {
  const recent2 = monthsWindow.slice(-2);
  const recent3 = monthsWindow.slice(-3);
  const paidMonths = monthsWindow.filter(m => {
    const p = getPayment(m, student.id);
    return p && p.paid;
  });
  const pattern = monthsWindow.map(m => paidMonths.includes(m));
  if (!paidMonths.length) {
    return { category: 'none', last: null, count: 0, pattern };
  }
  const last = paidMonths[paidMonths.length - 1];
  let category = 'suspicious';
  if (recent2.includes(last)) category = 'healthy';
  else if (recent3.includes(last)) category = 'fading';
  return { category, last, count: paidMonths.length, pattern };
}

function categoryTag(c) {
  if (c === 'healthy') return '<span class="status-tag status-active">健全</span>';
  if (c === 'fading') return '<span class="status-tag status-pause">注意</span>';
  if (c === 'suspicious') return '<span class="status-tag" style="background:rgba(239,68,68,0.18);color:var(--error)">辞めた可能性</span>';
  return '<span class="status-tag status-quit">未確認</span>';
}

function renderEnrollment() {
  const month = STATE.currentMonth;
  document.getElementById('enrollMonthTag').textContent = `基準: ${month}`;
  const months = lastNMonths(month, 6);

  const grade = document.getElementById('enrollGradeFilter')?.value || '';
  const course = document.getElementById('enrollCourseFilter')?.value || '';
  const cat = document.getElementById('enrollCategoryFilter')?.value || '';

  let students = activeStudents();
  const enriched = students.map(s => ({ s, ...categorizeStudent(s, months) }));

  // カテゴリ別カウント (フィルタ前の通塾全体)
  const counts = { healthy: 0, fading: 0, suspicious: 0, none: 0 };
  enriched.forEach(e => counts[e.category]++);
  document.getElementById('enrollCntHealthy').textContent = counts.healthy;
  document.getElementById('enrollCntFading').textContent = counts.fading;
  document.getElementById('enrollCntSuspicious').textContent = counts.suspicious;
  document.getElementById('enrollCntNone').textContent = counts.none;

  // フィルタ適用
  let visible = enriched;
  if (grade) visible = visible.filter(e => e.s.grade === grade);
  if (course) visible = visible.filter(e => (e.s.courses || []).includes(course));
  if (cat) visible = visible.filter(e => e.category === cat);

  // ソート: カテゴリ重要度 → 最終入金月 (古い順)
  const order = { suspicious: 0, none: 1, fading: 2, healthy: 3 };
  visible.sort((a, b) => {
    if (order[a.category] !== order[b.category]) return order[a.category] - order[b.category];
    return (a.last || '0').localeCompare(b.last || '0');
  });

  document.getElementById('enrollCountTag').textContent = `${visible.length}名 / ${activeStudents().length}名中`;

  const tbody = document.getElementById('enrollTbody');
  if (!visible.length) {
    tbody.innerHTML = `<tr><td colspan="11" class="empty">該当なし</td></tr>`;
    return;
  }

  tbody.innerHTML = visible.map(e => {
    const matrixCells = months.map((m, i) => {
      const cls = e.pattern[i] ? 'history-cell paid' : 'history-cell unpaid';
      const t = e.pattern[i] ? '✓' : '×';
      return `<span class="${cls}" title="${m}">${t}</span>`;
    }).join('');
    return `
      <tr data-student-id="${e.s.id}">
        <td class="ta-c"><input type="checkbox" class="enroll-check" value="${e.s.id}"></td>
        <td class="id-cell">#${e.s.id}</td>
        <td class="name-cell">${escapeHtml(e.s.name)}</td>
        <td>${escapeHtml(e.s.grade || '—')}</td>
        <td>${coursesTags(e.s.courses)}</td>
        <td class="ta-r fee-cell">${yen(e.s.fee)}</td>
        <td class="ta-c">${matrixCells}</td>
        <td>${e.last || '—'}</td>
        <td class="ta-c">${e.count}回</td>
        <td>${categoryTag(e.category)}</td>
        <td>${statusSelect(e.s)}</td>
      </tr>
    `;
  }).join('');

  tbody.onchange = (ev) => {
    const sel = ev.target.closest('select[data-action="status"]');
    if (!sel) return;
    const id = parseInt(sel.closest('tr').dataset.studentId, 10);
    setStatus(id, sel.value);
    sel.className = `status-select ${statusSelectClass(sel.value)}`;
    refresh();
  };
}

function bulkRetire() {
  const ids = [...document.querySelectorAll('.enroll-check:checked')].map(c => parseInt(c.value, 10));
  if (!ids.length) { alert('対象を選択してください'); return; }
  const names = ids.map(id => STATE.data.students.find(s => s.id === id)?.name).filter(Boolean);
  if (!confirm(`${ids.length}名を「退塾」に変更します。\n\n${names.slice(0, 8).join('、')}${names.length > 8 ? ` ... 他${names.length - 8}名` : ''}\n\n続行しますか？`)) return;
  ids.forEach(id => setStatus(id, '退塾'));
  alert(`✅ ${ids.length}名のステータスを退塾に変更しました`);
  populateAllFilters();
  refresh();
}

// === Phase 6: Dashboard ===

function renderDashboard() {
  const month = STATE.currentMonth;
  document.getElementById('dashMonthTag').textContent = month;

  // 当月入金状況
  const active = activeStudents();
  let paidCount = 0, paidAmount = 0, unpaidCount = 0, unpaidAmount = 0;
  active.forEach(s => {
    const pay = getPayment(month, s.id);
    if (pay && pay.paid) { paidCount++; paidAmount += s.fee || 0; }
    else { unpaidCount++; unpaidAmount += s.fee || 0; }
  });
  document.getElementById('dashTotal').textContent = active.length;
  document.getElementById('dashPaid').textContent = paidCount;
  document.getElementById('dashUnpaid').textContent = unpaidCount;
  document.getElementById('dashRevenue').textContent = yen(paidAmount);
  document.getElementById('dashOutstanding').textContent = yen(unpaidAmount);

  // 直近12ヶ月の月次売上 (paid 件のみカウント)
  const months = [];
  const cur = new Date(month + '-01');
  for (let i = 11; i >= 0; i--) {
    const d = new Date(cur.getFullYear(), cur.getMonth() - i, 1);
    months.push(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`);
  }

  const revenueData = months.map(m => {
    let total = 0;
    active.forEach(s => {
      const pay = getPayment(m, s.id);
      if (pay && pay.paid) total += pay.amount || s.fee || 0;
    });
    return total;
  });
  const rateData = months.map(m => {
    let p = 0, u = 0;
    active.forEach(s => {
      const pay = getPayment(m, s.id);
      if (pay && pay.paid) p++; else u++;
    });
    const tot = p + u;
    return tot ? Math.round(p / tot * 100) : 0;
  });

  // Course distribution
  const courseCount = {};
  active.forEach(s => {
    (s.courses || []).forEach(c => {
      courseCount[c] = (courseCount[c] || 0) + 1;
    });
  });
  const courseLabels = Object.keys(courseCount).sort((a, b) => courseCount[b] - courseCount[a]).slice(0, 12);
  const courseValues = courseLabels.map(c => courseCount[c]);

  drawChart('chartRevenue', 'revenue', {
    type: 'bar',
    data: {
      labels: months,
      datasets: [{
        label: '月次売上 (¥)',
        data: revenueData,
        backgroundColor: 'rgba(99,102,241,0.6)',
        borderColor: '#818cf8', borderWidth: 1,
      }],
    },
    options: chartOpts({ yCallback: v => '¥' + (v/1000).toFixed(0) + 'k' }),
  });

  drawChart('chartRate', 'rate', {
    type: 'line',
    data: {
      labels: months,
      datasets: [{
        label: '入金率 (%)',
        data: rateData,
        borderColor: '#10b981',
        backgroundColor: 'rgba(16,185,129,0.15)',
        fill: true, tension: 0.3, pointRadius: 3,
      }],
    },
    options: chartOpts({ yMax: 100, yCallback: v => v + '%' }),
  });

  drawChart('chartCourse', 'course', {
    type: 'doughnut',
    data: {
      labels: courseLabels,
      datasets: [{
        data: courseValues,
        backgroundColor: ['#6366f1','#ec4899','#10b981','#f59e0b','#0ea5e9','#8b5cf6','#ef4444','#14b8a6','#f97316','#a855f7','#06b6d4','#84cc16'],
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { position: 'right', labels: { color: '#9ca3af', font: { size: 10 } } } },
    },
  });
}

function chartOpts({ yMax, yCallback } = {}) {
  return {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      x: { ticks: { color: '#6b7280', font: { size: 10 } }, grid: { color: 'rgba(255,255,255,0.04)' } },
      y: {
        max: yMax,
        ticks: { color: '#6b7280', font: { size: 10 }, callback: yCallback || (v => v) },
        grid: { color: 'rgba(255,255,255,0.04)' },
      },
    },
  };
}

function drawChart(canvasId, key, config) {
  if (CHARTS[key]) CHARTS[key].destroy();
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  CHARTS[key] = new Chart(ctx, config);
}

// === Modal ===
function showModal(id) { document.getElementById(id).classList.remove('hidden'); }
function hideModal(id) { document.getElementById(id).classList.add('hidden'); }

function openSettings() {
  document.getElementById('setJukuName').value = SETTINGS.jukuName;
  document.getElementById('setOwnerName').value = SETTINGS.ownerName;
  document.getElementById('setOwnerEmail').value = SETTINGS.ownerEmail;
  document.getElementById('setOwnerPhone').value = SETTINGS.ownerPhone;
  document.getElementById('setBankName').value = SETTINGS.bankName;
  document.getElementById('setBranchName').value = SETTINGS.branchName;
  document.getElementById('setAccountType').value = SETTINGS.accountType;
  document.getElementById('setAccountNumber').value = SETTINGS.accountNumber;
  document.getElementById('setAccountHolder').value = SETTINGS.accountHolder;
  document.getElementById('setStripeCommon').value = SETTINGS.stripePaymentLink || '';

  // 月謝額別 Stripe リンクを動的生成
  const fees = [...new Set(STATE.data.students.filter(s => s.status === '通塾' && s.fee).map(s => s.fee))].sort((a, b) => a - b);
  const stripeContainer = document.getElementById('stripeFeeLinks');
  stripeContainer.innerHTML = fees.map(fee => `
    <label class="form-group">
      <span>¥${fee.toLocaleString('ja-JP')} 専用 (空欄=共通リンク使用)</span>
      <input type="url" data-stripe-fee="${fee}" placeholder="https://buy.stripe.com/..." value="${escapeHtml(SETTINGS.stripeLinksByFee?.[fee] || '')}">
    </label>
  `).join('');

  const dayEl = document.getElementById('setDeadlineDay');
  if (!dayEl.options.length) {
    for (let i = 1; i <= 28; i++) {
      const opt = document.createElement('option');
      opt.value = i; opt.textContent = i + '日';
      dayEl.appendChild(opt);
    }
  }
  dayEl.value = SETTINGS.deadlineDay;
  document.getElementById('setDunningTone').value = SETTINGS.dunningTone;
  document.getElementById('setMailSubject').value = SETTINGS.mailSubject;
  document.getElementById('setMailBody').value = SETTINGS.mailBody;
  showModal('settingsModal');
}

function saveSettingsFromForm() {
  SETTINGS.jukuName = document.getElementById('setJukuName').value.trim() || '◯◯塾';
  SETTINGS.ownerName = document.getElementById('setOwnerName').value.trim();
  SETTINGS.ownerEmail = document.getElementById('setOwnerEmail').value.trim();
  SETTINGS.ownerPhone = document.getElementById('setOwnerPhone').value.trim();
  SETTINGS.bankName = document.getElementById('setBankName').value.trim() || '楽天銀行';
  SETTINGS.branchName = document.getElementById('setBranchName').value.trim();
  SETTINGS.accountType = document.getElementById('setAccountType').value;
  SETTINGS.accountNumber = document.getElementById('setAccountNumber').value.trim();
  SETTINGS.accountHolder = document.getElementById('setAccountHolder').value.trim();
  SETTINGS.deadlineDay = parseInt(document.getElementById('setDeadlineDay').value, 10) || 25;
  SETTINGS.dunningTone = document.getElementById('setDunningTone').value;
  SETTINGS.mailSubject = document.getElementById('setMailSubject').value;
  SETTINGS.mailBody = document.getElementById('setMailBody').value;
  SETTINGS.stripePaymentLink = document.getElementById('setStripeCommon').value.trim();
  SETTINGS.stripeLinksByFee = {};
  document.querySelectorAll('[data-stripe-fee]').forEach(inp => {
    const v = inp.value.trim();
    if (v) SETTINGS.stripeLinksByFee[inp.dataset.stripeFee] = v;
  });
  saveSettings();
  hideModal('settingsModal');
  alert('✅ 設定を保存しました');
  refresh();
}

// === Init ===
function setupModals() {
  // 共通: closeボタン / オーバーレイクリックで閉じる
  document.querySelectorAll('.modal-overlay').forEach(ov => {
    ov.addEventListener('click', (e) => {
      if (e.target === ov || e.target.closest('[data-modal-close]')) {
        ov.classList.add('hidden');
      }
    });
  });

  // Settings
  document.getElementById('settingsBtn').addEventListener('click', openSettings);
  document.getElementById('saveSettingsBtn').addEventListener('click', saveSettingsFromForm);
  document.getElementById('resetSettingsBtn').addEventListener('click', () => {
    if (!confirm('メールテンプレートを初期値に戻しますか？')) return;
    document.getElementById('setMailSubject').value = DEFAULT_MAIL_SUBJECT;
    document.getElementById('setMailBody').value = DEFAULT_MAIL_BODY;
  });

  // Mail preview
  document.getElementById('mailSendBtn').addEventListener('click', (e) => {
    const id = parseInt(e.target.dataset.studentId, 10);
    sendMailTo(id);
    hideModal('mailPreviewModal');
    refresh();
  });
  document.getElementById('mailCopyBtn').addEventListener('click', () => {
    const subject = document.getElementById('mailPrevSubject').value;
    const body = document.getElementById('mailPrevBody').value;
    copyToClipboard(`件名: ${subject}\n\n${body}`);
    alert('📋 件名+本文をコピーしました');
  });

  // Bulk mail
  document.getElementById('bulkMailBtn').addEventListener('click', openBulkMailModal);
  document.getElementById('bulkSequentialBtn').addEventListener('click', bulkMailSequential);
  document.getElementById('bulkBccBtn').addEventListener('click', bulkMailBccCopy);
  document.getElementById('copyAllBccBtn').addEventListener('click', () => {
    const targets = bulkUnpaidWithEmail();
    if (!targets.length) { alert('メアド登録済の未払い者がいません'); return; }
    copyToClipboard(targets.map(s => getEmail(s.id)).join(', '));
    alert(`📋 ${targets.length}件のメアドをBCC形式でコピーしました`);
  });

  // Invoice
  document.getElementById('invoiceBulkBtn').addEventListener('click', bulkInvoicePDF);
  document.getElementById('invoicePreviewBtn').addEventListener('click', previewInvoicePDF);
  document.getElementById('invoiceDownloadBtn').addEventListener('click', (e) => {
    const id = parseInt(e.target.dataset.studentId, 10);
    if (id) generateInvoicePDF(id, true);
  });
  document.getElementById('invoiceSelectAll').addEventListener('change', (e) => {
    document.querySelectorAll('.invoice-check').forEach(c => c.checked = e.target.checked);
  });
  document.querySelectorAll('input[name="invoiceTarget"]').forEach(r => {
    r.addEventListener('change', renderInvoiceTab);
  });

  // Export / Import
  document.getElementById('exportBtn').addEventListener('click', exportAll);
  document.getElementById('importBtn').addEventListener('click', () => {
    document.getElementById('importFile').click();
  });
  document.getElementById('importFile').addEventListener('change', (e) => {
    const f = e.target.files[0]; if (f) importAll(f);
    e.target.value = '';
  });
}

async function init() {
  STATE.currentMonth = todayMonth();
  document.getElementById('monthInput').value = STATE.currentMonth;

  loadSettings();
  await loadData();
  populateAllFilters();
  refresh();

  document.getElementById('monthInput').addEventListener('change', (e) => {
    STATE.currentMonth = e.target.value;
    refresh();
  });
  document.getElementById('reloadBtn').addEventListener('click', async () => {
    await loadData();
    populateAllFilters();
    refresh();
  });
  document.querySelectorAll('.tab').forEach(t => {
    t.addEventListener('click', () => switchTab(t.dataset.tab));
  });
  document.getElementById('searchInput').addEventListener('input', renderAll);
  document.getElementById('statusFilter').addEventListener('change', renderAll);
  document.getElementById('gradeFilter').addEventListener('change', renderAll);
  document.getElementById('courseFilter').addEventListener('change', renderAll);
  document.getElementById('resetFilterBtn').addEventListener('click', () => {
    document.getElementById('searchInput').value = '';
    document.getElementById('statusFilter').value = '通塾';
    document.getElementById('gradeFilter').value = '';
    document.getElementById('courseFilter').value = '';
    renderAll();
  });
  document.getElementById('unpaidGradeFilter').addEventListener('change', renderUnpaid);
  document.getElementById('unpaidCourseFilter').addEventListener('change', renderUnpaid);
  document.getElementById('invoiceGradeFilter').addEventListener('change', renderInvoiceTab);
  document.getElementById('invoiceCourseFilter').addEventListener('change', renderInvoiceTab);

  // Enrollment
  ['enrollCategoryFilter','enrollGradeFilter','enrollCourseFilter'].forEach(id => {
    document.getElementById(id).addEventListener('change', renderEnrollment);
  });
  document.getElementById('enrollSelectAll').addEventListener('change', (e) => {
    document.querySelectorAll('.enroll-check').forEach(c => c.checked = e.target.checked);
  });
  document.getElementById('bulkRetireBtn').addEventListener('click', bulkRetire);

  setupImportUI();
  setupModals();
  document.getElementById('importMonthTag').textContent = `対象月: ${STATE.currentMonth}`;
}

init().then(() => {
  if (window._needsImport) showInitialImportBanner();
}).catch(err => {
  console.error(err);
  document.getElementById('unpaidTbody').innerHTML = `<tr><td colspan="8" class="empty">読込失敗: ${err.message}</td></tr>`;
});

function showInitialImportBanner() {
  if (document.getElementById('initial-import-banner')) return;
  const banner = document.createElement('div');
  banner.id = 'initial-import-banner';
  banner.style.cssText = `
    position: fixed; top: 0; left: 0; right: 0; z-index: 200;
    background: linear-gradient(135deg, #6366f1, #ec4899);
    color: white; padding: 1rem 1.5rem; font-size: 0.92rem;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    display: flex; justify-content: space-between; align-items: center; gap: 1rem;
  `;
  banner.innerHTML = `
    <div>
      <strong>📥 初回セットアップが必要です</strong><br>
      <span style="font-size:0.82rem;opacity:0.92">PCで💾エクスポートしたバックアップJSONを読み込んでください</span>
    </div>
    <button id="banner-import-btn" style="background:white;color:#6366f1;border:none;padding:0.6rem 1.2rem;border-radius:8px;font-weight:700;cursor:pointer;white-space:nowrap;">📂 ファイル選択</button>
  `;
  document.body.appendChild(banner);
  document.getElementById('banner-import-btn').onclick = () => {
    document.getElementById('importFile').click();
  };
}
