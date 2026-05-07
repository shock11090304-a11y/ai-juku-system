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

const DEFAULT_STRIPE_INVITE_SUBJECT = '【{{juku}}】月謝のカード決済 (毎月自動引き落とし) のご案内';
const DEFAULT_STRIPE_INVITE_BODY = `{{student}} 様の保護者様

平素より{{juku}}をご利用いただきありがとうございます。
塾長の{{owner}}でございます。

このたび月謝のお支払い方法に **クレジットカード (毎月自動引き落とし)** をご用意いたしました。
従来の銀行振込に加え、ご都合に合わせてお選びいただけます。

【自動引き落とし お申し込みURL】
{{paymentLink}}

上記URLよりカード情報を一度ご登録いただきますと、
**月謝 ¥{{fee}} (前払い制 / 翌月分を当月にお支払い)** を自動で毎月引き落とさせていただきます。
振込手数料はかからず、毎月の振込忘れの心配もございません。

▼カード情報の変更・解約 (24時間いつでも可能)
{{customerPortal}}

銀行振込を継続される場合は、引き続きこれまで通りで結構です。

ご不明な点がございましたら下記までお気軽にお問い合わせください。

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
  stripeCustomerPortalUrl: '',   // Stripe Customer Portal Login Link URL
  stripeInviteSubject: DEFAULT_STRIPE_INVITE_SUBJECT,
  stripeInviteBody: DEFAULT_STRIPE_INVITE_BODY,
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
const PW_KEY = 'juku-payment-pw-v1';

// AES-GCM 復号 (Web Crypto API)
async function decryptPayload(password, enc) {
  const b64 = (s) => Uint8Array.from(atob(s), c => c.charCodeAt(0));
  const salt = b64(enc.salt);
  const nonce = b64(enc.nonce);
  const ciphertext = b64(enc.ciphertext);
  const passKey = await crypto.subtle.importKey(
    'raw', new TextEncoder().encode(password),
    { name: 'PBKDF2' }, false, ['deriveKey']
  );
  const key = await crypto.subtle.deriveKey(
    { name: 'PBKDF2', salt, iterations: enc.iterations || 200000, hash: 'SHA-256' },
    passKey,
    { name: 'AES-GCM', length: 256 },
    false, ['decrypt']
  );
  const plaintext = await crypto.subtle.decrypt({ name: 'AES-GCM', iv: nonce }, key, ciphertext);
  return JSON.parse(new TextDecoder().decode(plaintext));
}

function promptPassword(errMsg) {
  return new Promise((resolve) => {
    const overlay = document.createElement('div');
    overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.85);display:grid;place-items:center;z-index:300;padding:1rem;backdrop-filter:blur(8px)';
    overlay.innerHTML = `
      <div style="background:#15152d;border:1px solid rgba(255,255,255,0.1);border-radius:16px;padding:2rem;max-width:420px;width:100%;box-shadow:0 20px 60px rgba(0,0,0,0.5)">
        <h2 style="font-size:1.15rem;margin-bottom:0.5rem;color:#e5e7eb">🔐 初回セットアップ</h2>
        <p style="color:#9ca3af;font-size:0.85rem;margin-bottom:1rem;line-height:1.6">塾長のメールに送付したパスワードを入力してください。<br>このデバイスでは1度だけ入力で済みます (以降は自動)。</p>
        ${errMsg ? `<p style="color:#ef4444;font-size:0.82rem;margin-bottom:0.85rem">⚠ ${errMsg}</p>` : ''}
        <input id="_pw_input" type="password" autofocus placeholder="パスワード"
          style="width:100%;background:rgba(0,0,0,0.4);border:1px solid #6366f1;color:#e5e7eb;padding:0.85rem;border-radius:8px;font-size:1rem;font-family:monospace;letter-spacing:0.08em;box-sizing:border-box" />
        <div style="display:flex;gap:0.5rem;margin-top:1rem;justify-content:flex-end">
          <button id="_pw_ok" style="background:linear-gradient(135deg,#6366f1,#818cf8);color:white;border:none;padding:0.7rem 1.4rem;border-radius:8px;cursor:pointer;font-weight:700;font-family:inherit;font-size:0.9rem">▶ 復号</button>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);
    const input = document.getElementById('_pw_input');
    const finish = (val) => { overlay.remove(); resolve(val); };
    input.onkeydown = (e) => { if (e.key === 'Enter') finish(input.value); };
    document.getElementById('_pw_ok').onclick = () => finish(input.value);
    setTimeout(() => input.focus(), 50);
  });
}

async function tryEncryptedFetch() {
  const res = await fetch('encrypted-data.json?t=' + Date.now());
  if (!res.ok) throw new Error('encrypted-data.json not found');
  const enc = await res.json();
  // 保存済パスワードでまず試行
  const cachedPw = localStorage.getItem(PW_KEY);
  if (cachedPw) {
    try {
      const payload = await decryptPayload(cachedPw, enc);
      return payload;
    } catch (e) { /* fall through to prompt */ }
  }
  // パスワード要求 (失敗したら再試行)
  let errMsg = '';
  for (let attempt = 0; attempt < 5; attempt++) {
    const pw = await promptPassword(errMsg);
    if (!pw) throw new Error('cancelled');
    try {
      const payload = await decryptPayload(pw, enc);
      localStorage.setItem(PW_KEY, pw);
      return payload;
    } catch (e) {
      errMsg = 'パスワードが違います。再入力してください。';
    }
  }
  throw new Error('パスワード認証失敗');
}

async function loadData() {
  // 1. localStorage キャッシュを最優先で使う
  const cached = localStorage.getItem(DATA_KEY);
  if (cached) {
    try { STATE.data = JSON.parse(cached); }
    catch { STATE.data = null; }
  }
  // 2. キャッシュなし → 平文 data.json (ローカル開発用) を先に試す
  if (!STATE.data) {
    try {
      const res = await fetch('data.json?t=' + Date.now());
      if (res.ok) {
        STATE.data = await res.json();
        localStorage.setItem(DATA_KEY, JSON.stringify(STATE.data));
      } else { throw new Error('plain not found'); }
    } catch (err) {
      // 3. 平文なし → 暗号化版を fetch + パスワード復号
      try {
        const payload = await tryEncryptedFetch();
        if (payload.data && payload.data.students) {
          STATE.data = payload.data;
          localStorage.setItem(DATA_KEY, JSON.stringify(STATE.data));
        }
        // overrides も同梱されていれば自動取り込み
        if (payload.overrides) {
          const exist = JSON.parse(localStorage.getItem(LS_KEY) || '{"payments":{},"emails":{},"payerNames":{},"mailSent":{},"status":{}}');
          const merged = {
            payments: { ...(exist.payments || {}) },
            emails: { ...(exist.emails || {}), ...(payload.overrides.emails || {}) },
            payerNames: { ...(exist.payerNames || {}), ...(payload.overrides.payerNames || {}) },
            mailSent: { ...(exist.mailSent || {}), ...(payload.overrides.mailSent || {}) },
            status: { ...(exist.status || {}), ...(payload.overrides.status || {}) },
          };
          for (const m of Object.keys(payload.overrides.payments || {})) {
            merged.payments[m] = { ...(merged.payments[m] || {}), ...payload.overrides.payments[m] };
          }
          localStorage.setItem(LS_KEY, JSON.stringify(merged));
        }
      } catch (e2) {
        STATE.data = { students: [], courses: [], payments: {}, nextStudentId: 1, nextCourseId: 1 };
        window._needsImport = true;
      }
    }
  }
  STATE.overrides = JSON.parse(localStorage.getItem(LS_KEY) || '{"payments":{},"emails":{},"payerNames":{},"mailSent":{}}');
  if (!STATE.overrides.payments) STATE.overrides.payments = {};
  if (!STATE.overrides.emails) STATE.overrides.emails = {};
  if (!STATE.overrides.payerNames) STATE.overrides.payerNames = {};
  if (!STATE.overrides.mailSent) STATE.overrides.mailSent = {};
  if (!STATE.overrides.status) STATE.overrides.status = {};
  if (!STATE.overrides.newStudents) STATE.overrides.newStudents = [];   // 2026-05-07: 生徒追加機能
  // newStudents を STATE.data.students に in-memory merge (id 重複は新生徒側を採用)
  mergeNewStudentsIntoData();
}

// 2026-05-07 追加: クラウド同期で取得した newStudents を data.json と合体する
function mergeNewStudentsIntoData() {
  if (!STATE.data || !STATE.data.students) return;
  const newStudents = STATE.overrides.newStudents || [];
  if (!newStudents.length) return;
  // 既存 id set
  const existingIds = new Set(STATE.data.students.map(s => s.id));
  for (const ns of newStudents) {
    if (!ns || typeof ns.id !== 'number') continue;
    if (!existingIds.has(ns.id)) {
      STATE.data.students.push(ns);
      existingIds.add(ns.id);
    }
  }
  // nextStudentId も追従 (= 次の追加で重複しないよう)
  const maxId = Math.max(STATE.data.nextStudentId || 1, ...newStudents.map(s => (s.id || 0) + 1));
  STATE.data.nextStudentId = maxId;
}

// 2026-05-07: モーダル閉じる safe helper (インライン style 上書き対策の二重保険)
function closeAddStudentModalSafe() {
  const m = document.getElementById('addStudentModal');
  if (!m) return;
  m.classList.add('hidden');
  m.style.display = 'none';   // ← class が効かなくても確実に消す
}
function openAddStudentModalSafe() {
  const m = document.getElementById('addStudentModal');
  if (!m) return;
  m.classList.remove('hidden');
  m.style.display = '';        // ← inline 削除で CSS 定義 (display: grid) を復活
}

// 2026-05-07 追加: 生徒追加モーダル — open
function openAddStudentModal() {
  const modal = document.getElementById('addStudentModal');
  if (!modal) return;
  // クリア + 入塾日 default = 今月
  document.getElementById('addStudentName').value = '';
  document.getElementById('addStudentGrade').value = '';
  document.getElementById('addStudentFee').value = '';
  document.getElementById('addStudentEmail').value = '';
  document.getElementById('addStudentPayerName').value = '';
  document.getElementById('addStudentCourses').value = '';
  document.getElementById('addStudentNotes').value = '';
  document.getElementById('addStudentEnrollDate').value = STATE.currentMonth || todayMonth();
  openAddStudentModalSafe();
  // フォーカス
  setTimeout(() => document.getElementById('addStudentName').focus(), 50);
}

// 2026-05-07 追加: 生徒追加モーダル — 保存
async function saveNewStudent() {
  const name = document.getElementById('addStudentName').value.trim();
  const grade = document.getElementById('addStudentGrade').value.trim();
  const feeRaw = document.getElementById('addStudentFee').value.trim();
  const email = document.getElementById('addStudentEmail').value.trim();
  const payerName = document.getElementById('addStudentPayerName').value.trim();
  const coursesRaw = document.getElementById('addStudentCourses').value.trim();
  const notes = document.getElementById('addStudentNotes').value.trim();
  const enrollDate = document.getElementById('addStudentEnrollDate').value.trim() || (STATE.currentMonth || todayMonth());

  if (!name) { alert('氏名は必須です'); return; }
  const fee = parseInt(feeRaw, 10);
  if (isNaN(fee) || fee < 0) { alert('月謝は 0 以上の整数を入力してください'); return; }
  // Reviewer A LOW #9: 極端な大値警告
  if (fee > 1000000) {
    if (!confirm(`月謝 ¥${fee.toLocaleString()} は通常より大きい値です。本当によろしいですか?`)) return;
  }
  // Reviewer A HIGH #4: 同名生徒の重複チェック (空白除去で正規化)
  const normName = name.replace(/[\s　]/g, '');
  const dup = STATE.data.students.find(s => (s.name || '').replace(/[\s　]/g, '') === normName);
  if (dup) {
    if (!confirm(`既に同名の生徒「${dup.name}」(ID #${dup.id}) が登録されています。\n本当に新規で追加しますか?\n(同姓同名なら OK / 兄弟登録ミス防止)`)) return;
  }

  // コース parse: カンマ or 改行 区切り
  const courses = coursesRaw
    ? coursesRaw.split(/[,、\n]/).map(s => s.trim()).filter(s => s)
    : [];

  // Reviewer A CRITICAL #1: id 発行 — newStudents の max も考慮 (= 同時追加で衝突防止)
  const usedIds = new Set(STATE.data.students.map(s => s.id));
  const newStudentsMax = (STATE.overrides.newStudents || []).reduce(
    (mx, s) => Math.max(mx, s.id || 0), 0
  );
  let id = Math.max(STATE.data.nextStudentId || 1, newStudentsMax + 1);
  while (usedIds.has(id)) id += 1;

  const newStudent = {
    id,
    name,
    grade: grade || '',
    email: email || '',
    courses,
    enrollDate,
    status: '通塾',
    fee,
    notes: notes || '',
    addedVia: 'add-student-modal',
    addedAt: new Date().toISOString(),
  };

  // overrides に保存 (= クラウド同期される)
  if (!STATE.overrides.newStudents) STATE.overrides.newStudents = [];
  STATE.overrides.newStudents.push(newStudent);
  // 振込人名は payerNames にも保存 (= マッチに使われる)
  if (payerName) {
    if (!STATE.overrides.payerNames) STATE.overrides.payerNames = {};
    STATE.overrides.payerNames[id] = payerName;
  }
  // メールも overrides.emails に保存
  if (email) {
    if (!STATE.overrides.emails) STATE.overrides.emails = {};
    STATE.overrides.emails[id] = email;
  }
  saveOverrides();          // localStorage 保存 + CloudSync push (debounced)

  // in-memory にも追加 (即時反映)
  STATE.data.students.push(newStudent);
  STATE.data.nextStudentId = id + 1;

  closeAddStudentModalSafe();
  populateAllFilters();
  refresh();

  // Reviewer A HIGH #5: 即時 push (debounce 待たずに) — タブ閉じ・通信不安定で消失防止
  let cloudMsg = '';
  if (typeof CloudSync !== 'undefined' && CloudSync.bootstrapped && CloudSync.getToken()) {
    const ok = await CloudSync.pushNow();
    cloudMsg = ok ? '✓ クラウド同期完了 (携帯/PC 共有)' : '⚠ クラウド同期失敗 (再試行は右上 ⚠ アイコンクリック)';
  } else {
    cloudMsg = 'ℹ クラウド未ログイン: localStorage のみに保存 (右上 🔒 をクリックでログインすると同期されます)';
  }
  alert(`✓ ${name} さん (ID #${id}) を追加しました。\n\n月謝 ¥${fee.toLocaleString()} / 学年 ${grade || '未設定'}\n\n${cloudMsg}`);
}

// Reviewer A HIGH #3: ESC キー + overlay クリックで閉じる
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    const m = document.getElementById('addStudentModal');
    if (m && !m.classList.contains('hidden')) closeAddStudentModalSafe();
  }
});
// overlay クリック (modal 外側 = overlay 自身) で閉じる
document.addEventListener('click', (e) => {
  const m = document.getElementById('addStudentModal');
  if (m && !m.classList.contains('hidden') && e.target === m) closeAddStudentModalSafe();
});

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

function getStripeInviteSent(studentId) {
  return STATE.overrides.stripeInviteSent?.[studentId] || null;
}
function setStripeInviteSent(studentId, isoDate) {
  if (!STATE.overrides.stripeInviteSent) STATE.overrides.stripeInviteSent = {};
  STATE.overrides.stripeInviteSent[studentId] = isoDate;
  saveOverrides();
}

function saveOverrides() {
  localStorage.setItem(LS_KEY, JSON.stringify(STATE.overrides));
  // 2026-05-07: クラウド sync (debounced 2 秒)
  if (typeof CloudSync !== 'undefined') CloudSync.schedulePush();
}

// =====================================================================
// 💴 クラウド sync (2026-05-07 追加)
// 携帯/PC 間で overrides (= 入金記録/メール/振込人名学習) を同期。
// 認証: ai-juku-system の admin Bearer token を流用 (既存 ADMIN_PASSWORD)。
// API: GET/POST /api/juku-payment/overrides
// =====================================================================
const ADMIN_TOKEN_KEY = 'juku-admin-bearer-v1';
const SYNC_LAST_KEY = 'juku-payment-sync-last-v1';   // ローカル最終 push 時刻
const API_BASE = (location.hostname === 'localhost' || location.hostname === '127.0.0.1')
  ? 'http://localhost:8000'
  : '';  // 同一オリジン (= /payment/ から /api/ へ相対)

// Reviewer A MEDIUM: JSON.parse バリデーション用 (= 期待される top-level key の whitelist)
const OVERRIDE_VALID_KEYS = new Set([
  'payments', 'emails', 'payerNames', 'mailSent', 'status', 'stripeInviteSent',
  'newStudents',   // 2026-05-07: 生徒追加機能
]);
function _isValidOverrides(obj) {
  if (!obj || typeof obj !== 'object' || Array.isArray(obj)) return false;
  for (const k of Object.keys(obj)) {
    if (!OVERRIDE_VALID_KEYS.has(k)) return false;
  }
  return true;
}

const CloudSync = {
  pushTimer: null,
  status: 'init',          // 'init' | 'syncing' | 'ok' | 'auth-required' | 'error' | 'disabled'
  lastPushAt: 0,
  lastPullAt: 0,
  errorMsg: '',
  bootstrapped: false,     // Reviewer A CRITICAL #2: bootstrap 完了まで push を suppress

  getToken() { return localStorage.getItem(ADMIN_TOKEN_KEY) || ''; },
  setToken(t) { if (t) localStorage.setItem(ADMIN_TOKEN_KEY, t); },
  clearToken() { localStorage.removeItem(ADMIN_TOKEN_KEY); },

  async login(password) {
    try {
      const res = await fetch(`${API_BASE}/api/admin/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password }),
      });
      const data = await res.json();
      if (res.ok && data.token) {
        this.setToken(data.token);
        this.status = 'ok';
        this.errorMsg = '';
        updateSyncStatusBar();
        return true;
      }
      this.errorMsg = data.detail || 'パスワードが違います';
      return false;
    } catch (e) {
      this.errorMsg = e.message;
      return false;
    }
  },

  async pull() {
    const token = this.getToken();
    if (!token) { this.status = 'auth-required'; updateSyncStatusBar(); return null; }
    this.status = 'syncing'; updateSyncStatusBar();
    try {
      const res = await fetch(`${API_BASE}/api/juku-payment/overrides`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (res.status === 401) {
        this.clearToken();
        this.status = 'auth-required';
        updateSyncStatusBar();
        return null;
      }
      if (!res.ok) {
        this.status = 'error';
        this.errorMsg = `pull ${res.status}`;
        updateSyncStatusBar();
        return null;
      }
      const data = await res.json();
      this.lastPullAt = Date.now();
      this.status = 'ok';
      updateSyncStatusBar();
      return data;  // { ok, value (JSON string), updated_at, exists }
    } catch (e) {
      this.status = 'error';
      this.errorMsg = e.message;
      updateSyncStatusBar();
      return null;
    }
  },

  schedulePush() {
    // Reviewer A CRITICAL #2: bootstrap 完了前は push しない (= remote 取得前に local を上書きされるのを防ぐ)
    if (!this.bootstrapped) return;
    // 2 秒 debounce — 連続編集を 1 リクエストにまとめる
    if (this.pushTimer) clearTimeout(this.pushTimer);
    this.pushTimer = setTimeout(() => this.pushNow(), 2000);
  },

  // Reviewer A CRITICAL #1 / LOW #7: ページ離脱時に debounce flush
  // sendBeacon で同期 (= 確実に届く・ブラウザがタブを閉じても OK)
  flushSync() {
    if (this.pushTimer) { clearTimeout(this.pushTimer); this.pushTimer = null; }
    const token = this.getToken();
    if (!token || !this.bootstrapped) return;
    try {
      const value = JSON.stringify(STATE.overrides || {});
      // sendBeacon は header が付かないため、custom auth は不可。fetch keepalive で代用。
      fetch(`${API_BASE}/api/juku-payment/overrides`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ value }),
        keepalive: true,
      }).catch(() => {});  // 離脱中なので結果は気にしない
    } catch (e) { /* ignore */ }
  },

  async pushNow() {
    const token = this.getToken();
    if (!token) { this.status = 'auth-required'; updateSyncStatusBar(); return false; }
    this.status = 'syncing'; updateSyncStatusBar();
    try {
      // Reviewer A CRITICAL #2: pull-merge-push で newStudents 配列の同時追加消失を防ぐ
      // 同時に別デバイスで生徒追加された場合、単純な POST だと array overwrite で消失する。
      // → push 直前に pull → 自分にない newStudents を merge (id unique) → POST
      try {
        const pullRes = await fetch(`${API_BASE}/api/juku-payment/overrides`, {
          headers: { 'Authorization': `Bearer ${token}` },
        });
        if (pullRes.ok) {
          const data = await pullRes.json();
          if (data.exists && data.value) {
            const remoteOv = JSON.parse(data.value);
            if (_isValidOverrides(remoteOv) && Array.isArray(remoteOv.newStudents)) {
              const localIds = new Set((STATE.overrides.newStudents || []).map(s => s.id));
              const toAdd = remoteOv.newStudents.filter(s => s && typeof s.id === 'number' && !localIds.has(s.id));
              if (toAdd.length) {
                STATE.overrides.newStudents = (STATE.overrides.newStudents || []).concat(toAdd);
                localStorage.setItem(LS_KEY, JSON.stringify(STATE.overrides));
                if (typeof mergeNewStudentsIntoData === 'function') mergeNewStudentsIntoData();
                if (typeof populateAllFilters === 'function') populateAllFilters();
                if (typeof refresh === 'function') refresh();
                console.log('[CloudSync] pushNow: merged', toAdd.length, 'remote newStudents before push');
              }
            }
          }
        }
      } catch (e) { console.warn('[CloudSync] pre-push pull failed:', e); /* push は続行 */ }

      const value = JSON.stringify(STATE.overrides || {});
      const res = await fetch(`${API_BASE}/api/juku-payment/overrides`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ value }),
      });
      if (res.status === 401) {
        this.clearToken();
        this.status = 'auth-required';
        updateSyncStatusBar();
        return false;
      }
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        this.status = 'error';
        this.errorMsg = data.detail || `push ${res.status}`;
        updateSyncStatusBar();
        return false;
      }
      const data = await res.json();
      this.lastPushAt = Date.now();
      localStorage.setItem(SYNC_LAST_KEY, String(this.lastPushAt));
      this.status = 'ok';
      updateSyncStatusBar();
      return true;
    } catch (e) {
      this.status = 'error';
      this.errorMsg = e.message;
      updateSyncStatusBar();
      return false;
    }
  },

  async bootstrap() {
    // ページロード直後に呼ぶ。token があれば pull → local 上書き。
    const token = this.getToken();
    if (!token) { this.status = 'auth-required'; updateSyncStatusBar(); this.bootstrapped = true; return; }
    const remote = await this.pull();
    if (remote && remote.exists && remote.value) {
      try {
        const remoteOverrides = JSON.parse(remote.value);
        // Reviewer A MEDIUM: 期待されない top-level key が混在してたら拒否 (= corrupted remote 防御)
        if (_isValidOverrides(remoteOverrides)) {
          STATE.overrides = remoteOverrides;
          // overrides 既定キーを補完 (= 後方互換)
          if (!STATE.overrides.payments) STATE.overrides.payments = {};
          if (!STATE.overrides.emails) STATE.overrides.emails = {};
          if (!STATE.overrides.payerNames) STATE.overrides.payerNames = {};
          if (!STATE.overrides.mailSent) STATE.overrides.mailSent = {};
          if (!STATE.overrides.status) STATE.overrides.status = {};
          if (!STATE.overrides.newStudents) STATE.overrides.newStudents = [];
          localStorage.setItem(LS_KEY, JSON.stringify(STATE.overrides));
          // remote 側の newStudents を STATE.data.students に in-memory merge (= 別デバイスで追加した生徒を取り込む)
          mergeNewStudentsIntoData();
        } else {
          console.warn('[CloudSync] remote overrides shape invalid, ignoring:', Object.keys(remoteOverrides));
          this.errorMsg = 'remote データ形式不正 (= 古い/壊れたデータ。push で上書きします)';
        }
      } catch (e) {
        console.warn('[CloudSync] remote JSON parse failed:', e);
        this.errorMsg = 'remote JSON parse 失敗';
      }
    } else if (remote && !remote.exists) {
      // remote 未作成 = 初回 → 現在の local を push して作成 (bootstrap 完了後に schedulePush が動くよう先に flag 立てる)
      this.bootstrapped = true;
      await this.pushNow();
      return;
    }
    this.bootstrapped = true;
  },
};

// Reviewer A CRITICAL #1 / LOW #7: ページ離脱時に debounce flush
window.addEventListener('pagehide', () => CloudSync.flushSync());
window.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'hidden') CloudSync.flushSync();
});

// クラウド同期ステータスバー (2026-05-07: position:fixed から header 内ボタンに変更)
// 旧版は画面右上に常時オーバーレイ表示で生徒一覧の右端を遮蔽していたため、ヘッダー内に統合。
function updateSyncStatusBar() {
  // 旧バー (position:fixed) が DOM に残っていたら削除 (= バックワード互換)
  const oldFixed = document.getElementById('cloudSyncBar');
  if (oldFixed && oldFixed.style.position === 'fixed') oldFixed.remove();

  const btn = document.getElementById('cloudSyncBtn');
  if (!btn) return;
  // クリックハンドラを 1 回だけ bind
  if (!btn.dataset.bound) {
    btn.addEventListener('click', () => {
      if (CloudSync.status === 'auth-required') {
        promptAdminLogin();
      } else if (CloudSync.status === 'error') {
        alert(`同期エラー: ${CloudSync.errorMsg}\n\nOK で再試行します。`);
        CloudSync.pushNow();
      } else {
        // 強制 push
        CloudSync.pushNow();
      }
    });
    btn.dataset.bound = '1';
  }
  const s = CloudSync.status;
  const map = {
    'init':          { txt: '☁ 初期化',     title: 'クラウド同期初期化中…' },
    'syncing':       { txt: '⏳ 同期中',     title: 'サーバーと同期中…' },
    'ok':            { txt: '✓ 同期済',      title: 'クラウド同期 OK (クリックで強制 push)' },
    'auth-required': { txt: '🔒 ログイン',  title: 'クリックで管理者ログイン' },
    'error':         { txt: '⚠ エラー',     title: `同期エラー: ${CloudSync.errorMsg || '不明'} (クリックで再試行)` },
    'disabled':      { txt: '☁ OFF',        title: 'クラウド同期 OFF' },
  };
  const cfg = map[s] || map['init'];
  btn.textContent = cfg.txt;
  btn.title = cfg.title;
  // 状態別の色 (= 既存 .btn-ghost の上に色だけ重ねる)
  btn.style.color = (s === 'ok') ? '#34d399'
                  : (s === 'syncing') ? '#a5b4fc'
                  : (s === 'auth-required') ? '#fbbf24'
                  : (s === 'error') ? '#fca5a5'
                  : '';
}

// 管理者ログインモーダル (シンプルな prompt 派生)
async function promptAdminLogin() {
  const pw = prompt('クラウド同期を有効にするには、管理者パスワードを入力してください。\n(ai-juku-system の ADMIN_PASSWORD と同じ)');
  if (pw === null) return;
  if (!pw) { alert('パスワードを入力してください'); return; }
  const ok = await CloudSync.login(pw);
  if (ok) {
    alert('✓ ログイン成功。クラウド同期を開始します。');
    // 既存データを pull (= 別デバイスで作業した結果を取り込む)
    const remote = await CloudSync.pull();
    if (remote && remote.exists && remote.value) {
      try {
        STATE.overrides = JSON.parse(remote.value);
        // 既定キー補完
        if (!STATE.overrides.payments) STATE.overrides.payments = {};
        if (!STATE.overrides.emails) STATE.overrides.emails = {};
        if (!STATE.overrides.payerNames) STATE.overrides.payerNames = {};
        if (!STATE.overrides.mailSent) STATE.overrides.mailSent = {};
        if (!STATE.overrides.status) STATE.overrides.status = {};
        if (!STATE.overrides.newStudents) STATE.overrides.newStudents = [];
        localStorage.setItem(LS_KEY, JSON.stringify(STATE.overrides));
        // 別デバイスで追加した生徒を in-memory merge
        if (typeof mergeNewStudentsIntoData === 'function') mergeNewStudentsIntoData();
        if (typeof populateAllFilters === 'function') populateAllFilters();
        if (typeof refresh === 'function') refresh();
      } catch (e) {}
    } else {
      // 初回 → 現在の local を push
      await CloudSync.pushNow();
    }
  } else {
    alert(`ログイン失敗: ${CloudSync.errorMsg}`);
  }
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

// 2026-05-07 追加: 即反映ボタン用の Undo トースト
// 10 秒以内に「取消」をクリックすると入金状態を元に戻す。
// keyframe 「toastInCentered」をグローバル注入 (1回のみ・既存 slideUp と translateX 衝突するため専用)
(function ensureToastKeyframe() {
  if (document.getElementById('instantPayToastKeyframe')) return;
  const style = document.createElement('style');
  style.id = 'instantPayToastKeyframe';
  style.textContent = `@keyframes toastInCentered { from { transform: translate(-50%, 20px); opacity: 0; } to { transform: translate(-50%, 0); opacity: 1; } }`;
  document.head.appendChild(style);
})();

function showInstantPayUndoToast(month, studentId, name) {
  // 既存トーストがあれば消す
  const old = document.getElementById('instantPayToast');
  if (old) old.remove();
  const toast = document.createElement('div');
  toast.id = 'instantPayToast';
  // Reviewer B CRITICAL: translateX(-50%) を keyframe (translate(-50%, ...)) で保持
  toast.style.cssText = 'position:fixed;bottom:24px;left:50%;transform:translate(-50%, 0);background:linear-gradient(135deg,#10b981,#059669);color:#fff;padding:12px 18px;border-radius:10px;box-shadow:0 8px 24px rgba(0,0,0,0.25);font-size:0.9rem;font-weight:600;z-index:9999;display:flex;align-items:center;gap:14px;flex-wrap:wrap;max-width:calc(100vw - 32px);animation:toastInCentered 0.25s ease-out';
  toast.innerHTML = `
    <span>✓ ${escapeHtml(name)} さんを ${month} 入金済として記録しました</span>
    <button id="instantPayUndoBtn" style="background:rgba(255,255,255,0.22);border:1px solid rgba(255,255,255,0.4);color:#fff;padding:5px 12px;border-radius:6px;font-weight:700;cursor:pointer;font-size:0.85rem">↩ 取消</button>
    <span id="instantPayCountdown" style="font-size:0.78rem;opacity:0.85">10秒後に閉じる</span>
  `;
  document.body.appendChild(toast);
  // カウントダウン + 自動消去
  let secs = 10;
  const cd = toast.querySelector('#instantPayCountdown');
  const interval = setInterval(() => {
    secs -= 1;
    if (cd) cd.textContent = `${secs}秒後に閉じる`;
    if (secs <= 0) {
      clearInterval(interval);
      toast.remove();
    }
  }, 1000);
  // 取消ハンドラ: setPayment を unpaid に戻す + delete override
  toast.querySelector('#instantPayUndoBtn').addEventListener('click', () => {
    clearInterval(interval);
    // setPayment(month, id, false) では override が「未払い」として残ってしまうため、override 自体を削除
    if (STATE.overrides.payments[month] && STATE.overrides.payments[month][studentId] !== undefined) {
      delete STATE.overrides.payments[month][studentId];
      saveOverrides();
    }
    refresh();
    toast.remove();
  });
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
// Stripe 登録顧客キャッシュ (60秒)
const STRIPE_CUST_CACHE = { customers: [], loadedAt: 0, loading: false };

async function loadRegisteredCustomers(force = false) {
  const now = Date.now();
  if (!force && STRIPE_CUST_CACHE.loadedAt && now - STRIPE_CUST_CACHE.loadedAt < 60000) return STRIPE_CUST_CACHE.customers;
  if (STRIPE_CUST_CACHE.loading) return STRIPE_CUST_CACHE.customers;
  const pw = (typeof CHAT_STATE !== 'undefined' && CHAT_STATE.pw) || localStorage.getItem('juku-chat-pw-v1') || '';
  if (!pw) return [];
  STRIPE_CUST_CACHE.loading = true;
  try {
    const res = await fetch('/payment/api/registered-customers', { headers: { 'X-Admin-Password': pw } });
    if (!res.ok) { STRIPE_CUST_CACHE.loading = false; return []; }
    const data = await res.json();
    STRIPE_CUST_CACHE.customers = data.customers || [];
    STRIPE_CUST_CACHE.loadedAt = now;
  } catch (e) {
    console.warn('loadRegisteredCustomers failed:', e);
  } finally {
    STRIPE_CUST_CACHE.loading = false;
  }
  return STRIPE_CUST_CACHE.customers;
}

// 生徒名から Stripe Customer をマッチ (matchPayer の正規化を流用)
function matchCustomerForStudent(student) {
  if (!STRIPE_CUST_CACHE.customers.length) return null;
  const sNorm = normalizeName(student.name);
  if (!sNorm) return null;
  // Layer 1: 完全一致 (各候補名)
  for (const c of STRIPE_CUST_CACHE.customers) {
    const cNorm = normalizeName(c.studentName);
    if (cNorm && cNorm === sNorm) return c;
  }
  // Layer 2: 部分一致
  for (const c of STRIPE_CUST_CACHE.customers) {
    const cNorm = normalizeName(c.studentName);
    if (cNorm && (cNorm.includes(sNorm) || sNorm.includes(cNorm))) return c;
  }
  // Layer 3: 括弧内候補との完全一致
  const sCands = extractNameCandidates(student.name).map(normalizeName).filter(Boolean);
  for (const c of STRIPE_CUST_CACHE.customers) {
    const cCands = extractNameCandidates(c.studentName).map(normalizeName).filter(Boolean);
    for (const sc of sCands) {
      for (const cc of cCands) {
        if (sc === cc) return c;
      }
    }
  }
  return null;
}

async function renderUnpaid() {
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

  // Stripe 登録顧客 (バックグラウンドで読込、結果は次の renderUnpaid で反映)
  loadRegisteredCustomers().then(() => updateStripeStatusBar(unpaid));
  updateStripeStatusBar(unpaid);

  if (!unpaid.length) {
    tbody.innerHTML = `<tr><td colspan="8" class="empty">🎉 ${month} の未払い者はいません</td></tr>`;
    return;
  }

  tbody.innerHTML = unpaid.map(s => {
    const sent = getMailSent(month, s.id);
    const email = getEmail(s.id);
    const stripeCust = matchCustomerForStudent(s);
    const stripeBadge = stripeCust
      ? `<span class="badge" style="background:rgba(16,185,129,0.18); color:#34d399; padding:2px 8px; border-radius:6px; font-size:0.78rem; font-weight:600;" title="${escapeHtml(stripeCust.customerId)}">✓ 登録済</span>`
      : `<span class="badge" style="background:rgba(107,114,128,0.18); color:#9ca3af; padding:2px 8px; border-radius:6px; font-size:0.78rem;">未登録</span>`;
    const status = sent
      ? `<span class="mail-status mail-sent">✓ ${sent} 送信済</span>`
      : email
        ? `<span class="mail-status mail-pending">未送信</span>`
        : `<span class="mail-status">メール未登録</span>`;
    return `
    <tr data-student-id="${s.id}" data-stripe-customer="${stripeCust ? escapeHtml(stripeCust.customerId) : ''}">
      <td class="id-cell">#${s.id}</td>
      <td class="name-cell">${escapeHtml(s.name)}</td>
      <td>${escapeHtml(s.grade || '—')}</td>
      <td class="ta-r fee-cell">${yen(s.fee)}</td>
      <td><input type="text" class="email-input" data-action="email" placeholder="メール未登録" value="${escapeHtml(email)}"></td>
      <td class="ta-c">${stripeBadge}</td>
      <td class="ta-c">${status}</td>
      <td class="ta-c">
        <div class="mail-actions">
          <button class="icon-btn" data-action="mail-preview" title="メール内容を確認">📧 確認</button>
          <button class="icon-btn ${sent ? 'icon-btn-success' : ''}" data-action="mail-send" title="メーラーで開く" ${email ? '' : 'disabled'}>${sent ? '✓ 送信' : '➜ 送信'}</button>
          ${stripeCust ? `<button class="icon-btn" data-action="past-due-one" title="この生徒に Stripe 請求書を発行">💳 請求書</button>` : ''}
          <button class="btn btn-primary btn-sm pay-toggle" data-action="toggle" title="入金済にする (即時反映・取消可)">💴 入金あり</button>
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
      // 2026-05-07: 即反映ボタン格上げ — 確認 dialog + 取消トースト
      const student = activeStudents().find(x => x.id === id);
      if (!student) {
        alert('生徒情報が見つかりません。画面を再読込してください。');
        return;
      }
      const name = student.name;
      const fee = student.fee || 0;
      const monthJp = month.replace(/^(\d{4})-(\d{2})$/, '$1年$2月');
      const feeMsg = fee > 0 ? `¥${fee.toLocaleString()}` : '¥0 (※月謝額が未設定です)';
      const ok = confirm(`${name} さんの ${monthJp}月謝 ${feeMsg} を入金済として記録しますか?\n\n(振込日: 今日 / 摘要: 手動チェック)\n\n反映後 10 秒以内なら下部のトーストで取消できます。`);
      if (!ok) return;
      setPayment(month, id, true, new Date().toISOString().slice(0, 10), '手動チェック', null);
      refresh();
      showInstantPayUndoToast(month, id, name);
    } else if (a === 'mail-preview') {
      openMailPreview(id);
    } else if (a === 'mail-send') {
      sendMailTo(id);
      renderUnpaid();
    } else if (a === 'past-due-one') {
      sendPastDueInvoiceFor(id);
    }
  };
  tbody.oninput = (e) => {
    const t = e.target;
    const tr = t.closest('tr'); if (!tr) return;
    const id = parseInt(tr.dataset.studentId, 10);
    if (t.dataset.action === 'email') setEmail(id, t.value.trim());
  };
}

function updateStripeStatusBar(unpaid) {
  const bar = document.getElementById('stripeStatusBar');
  const text = document.getElementById('stripeStatusText');
  const btn = document.getElementById('bulkPastDueBtn');
  if (!bar || !text) return;
  const total = STRIPE_CUST_CACHE.customers.length;
  if (total === 0) {
    bar.style.display = 'block';
    text.textContent = `💳 Stripe 登録者: 0 名 — まだカード登録した保護者がいません (登録 URL: /payment/register.html)`;
    if (btn) btn.disabled = true;
    return;
  }
  const matchedCount = unpaid.filter(s => matchCustomerForStudent(s)).length;
  bar.style.display = 'block';
  text.innerHTML = `💳 Stripe 登録者 <strong>${total}名</strong> 中、当月未払い者で登録済みは <strong style="color:#34d399;">${matchedCount}名</strong> / 未登録 <strong style="color:#9ca3af;">${unpaid.length - matchedCount}名</strong>`;
  if (btn) btn.disabled = matchedCount === 0;
}

async function sendPastDueInvoiceFor(studentId) {
  const s = STATE.data.students.find(x => x.id === studentId);
  if (!s) return;
  const cust = matchCustomerForStudent(s);
  if (!cust) { alert('この生徒は Stripe 未登録です'); return; }
  const month = STATE.currentMonth;
  const fee = s.fee || 0;
  if (!fee) { alert('月謝額が 0 円です'); return; }
  if (!confirm(`#${s.id} ${s.name} に ${month} 分の請求書を発行します。\n\n金額: ¥${fee.toLocaleString()}\n送信先: ${cust.email || '(Stripe 登録時メアド)'}\n支払期限: 7 日後\n\n保護者の登録メアド宛に Stripe から自動でメール送信されます。\n同じ生徒・同月の重複発行は自動で防がれます (90日間)。\n続行しますか?`)) return;

  const pw = (typeof CHAT_STATE !== 'undefined' && CHAT_STATE.pw) || localStorage.getItem('juku-chat-pw-v1') || '';
  if (!pw) { alert('管理パスワード未入力です。チャットタブで入力してください。'); switchTab('chat'); return; }

  // 二重送信防止: 同一行のボタンを一時 disabled
  const btn = document.querySelector(`tr[data-student-id="${studentId}"] [data-action="past-due-one"]`);
  if (btn) { if (btn.dataset.busy === '1') return; btn.dataset.busy = '1'; btn.disabled = true; const orig = btn.textContent; btn.textContent = '⏳'; }
  try {
    const res = await fetch('/payment/api/past-due-invoice', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Admin-Password': pw },
      body: JSON.stringify({ items: [{ customerId: cust.customerId, studentName: s.name, month, amount: fee, description: `AI学習コーチ塾 ${month} 月謝` }] }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) { alert(`エラー: ${data.message || data.error || 'unknown'}`); return; }
    const r = (data.results || [])[0] || {};
    if (r.status === 'success') {
      alert(`✓ 請求書発行完了\n\nInvoice ID: ${r.invoiceId}\n金額: ¥${r.amountDue.toLocaleString()}\n\nStripe から保護者宛にメール送信されました。`);
    } else if (r.status === 'duplicate') {
      alert(`⚠ 既に発行済み\n\nこの生徒の ${month} 分は既に請求書が発行されています。\nInvoice ID: ${r.invoiceId}\n\n90日経過後または別月であれば再発行できます。`);
    } else {
      alert(`発行失敗: ${r.error || 'unknown'}`);
    }
  } finally {
    if (btn) { btn.dataset.busy = ''; btn.disabled = false; btn.textContent = '💳 請求書'; }
  }
}

async function sendBulkPastDueInvoices() {
  const btn = document.getElementById('bulkPastDueBtn');
  if (btn?.dataset.busy === '1') return;  // 二重送信防止
  const month = STATE.currentMonth;
  const grade = document.getElementById('unpaidGradeFilter')?.value || '';
  const course = document.getElementById('unpaidCourseFilter')?.value || '';
  let unpaid = activeStudents().filter(s => {
    const pay = getPayment(month, s.id);
    return !pay || !pay.paid;
  });
  if (grade) unpaid = unpaid.filter(s => s.grade === grade);
  if (course) unpaid = unpaid.filter(s => (s.courses || []).includes(course));

  await loadRegisteredCustomers(true);
  const items = [];
  for (const s of unpaid) {
    const cust = matchCustomerForStudent(s);
    if (cust && cust.customerId && (s.fee || 0) > 0) {
      items.push({ customerId: cust.customerId, studentName: s.name, month, amount: s.fee, description: `AI学習コーチ塾 ${month} 月謝` });
    }
  }
  if (!items.length) { alert(`Stripe 登録済の未払い者がいません (${month})`); return; }
  const total = items.reduce((sum, i) => sum + i.amount, 0);
  // 個別金額を含む詳細 confirm
  const itemList = items.slice(0, 10).map(i => `  • ${i.studentName} ¥${i.amount.toLocaleString()}`).join('\n');
  const more = items.length > 10 ? `\n  ...他 ${items.length - 10} 名` : '';
  if (!confirm(`【${month} 分 Stripe 請求書 一括発行】\n\n対象: ${items.length} 名\n合計: ¥${total.toLocaleString()}\n支払期限: 発行から 7 日後\n\n${itemList}${more}\n\n各保護者の Stripe 登録メアド宛に Stripe からメール送信されます。\n同じ生徒・同月の重複発行は自動で防がれます (90日間)。\n\n続行しますか?`)) return;

  const pw = (typeof CHAT_STATE !== 'undefined' && CHAT_STATE.pw) || localStorage.getItem('juku-chat-pw-v1') || '';
  if (!pw) { alert('管理パスワード未入力。チャットタブで入力してください。'); switchTab('chat'); return; }

  if (btn) {
    btn.dataset.busy = '1';
    btn.disabled = true;
    btn.textContent = '⏳ 発行中…';
  }
  try {
    const res = await fetch('/payment/api/past-due-invoice', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Admin-Password': pw },
      body: JSON.stringify({ items }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) { alert(`エラー: ${data.message || data.error || 'unknown'}`); return; }
    const ok = data.summary?.success || 0;
    const ng = data.summary?.failed || 0;
    const dup = (data.results || []).filter(r => r.status === 'duplicate').length;
    let detail = '';
    if (ng > 0) {
      const failures = (data.results || []).filter(r => r.status === 'error');
      if (failures.length) detail += '\n\n失敗詳細:\n' + failures.slice(0, 15).map(r => `  ⚠ ${r.studentName}: ${r.error}`).join('\n');
    }
    if (dup > 0) {
      detail += `\n\n重複スキップ: ${dup} 名 (既に同月分発行済)`;
    }
    alert(`完了\n  成功: ${ok}/${items.length}\n  失敗: ${ng}\n  重複スキップ: ${dup}${detail}`);
  } finally {
    if (btn) {
      btn.dataset.busy = '';
      btn.disabled = false;
      btn.textContent = '💳 Stripe請求書一括';
    }
  }
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
  else if (name === 'communication') renderCommunication();
  else if (name === 'chat') renderChat();
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
  else if (active === 'communication') renderCommunication();
  else if (active === 'chat') renderChat();
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

const HW_KANA_MAP = {
  'ｦ':'ヲ','ｧ':'ァ','ｨ':'ィ','ｩ':'ゥ','ｪ':'ェ','ｫ':'ォ',
  'ｬ':'ャ','ｭ':'ュ','ｮ':'ョ','ｯ':'ッ','ｰ':'ー',
  'ｱ':'ア','ｲ':'イ','ｳ':'ウ','ｴ':'エ','ｵ':'オ',
  'ｶ':'カ','ｷ':'キ','ｸ':'ク','ｹ':'ケ','ｺ':'コ',
  'ｻ':'サ','ｼ':'シ','ｽ':'ス','ｾ':'セ','ｿ':'ソ',
  'ﾀ':'タ','ﾁ':'チ','ﾂ':'ツ','ﾃ':'テ','ﾄ':'ト',
  'ﾅ':'ナ','ﾆ':'ニ','ﾇ':'ヌ','ﾈ':'ネ','ﾉ':'ノ',
  'ﾊ':'ハ','ﾋ':'ヒ','ﾌ':'フ','ﾍ':'ヘ','ﾎ':'ホ',
  'ﾏ':'マ','ﾐ':'ミ','ﾑ':'ム','ﾒ':'メ','ﾓ':'モ',
  'ﾔ':'ヤ','ﾕ':'ユ','ﾖ':'ヨ',
  'ﾗ':'ラ','ﾘ':'リ','ﾙ':'ル','ﾚ':'レ','ﾛ':'ロ',
  'ﾜ':'ワ','ﾝ':'ン',
};

const IMPORT = { rows: [], candidates: [], filterTab: 'pending' };

function normalizeName(raw) {
  if (!raw) return '';
  let s = String(raw);
  s = s.replace(/[ｦ-ﾝ]/g, c => HW_KANA_MAP[c] || c);
  s = s.replace(/(.)[゛ﾞ]/g, (m, c) => DAKUTEN[c] || c);
  s = s.replace(/(.)[゜ﾟ]/g, (m, c) => HANDAKUTEN[c] || c);
  s = s.replace(/[ァ-ヶ]/g, m => String.fromCharCode(m.charCodeAt(0) - 0x60));
  s = s.replace(/づ/g, 'ず').replace(/ぢ/g, 'じ');
  s = s.replace(/[\s　]+/g, '');
  s = s.replace(/(英語(塾代|代|月謝)?|月謝|塾代)$/, '');
  s = s.toLowerCase();
  return s;
}

function extractNameCandidates(rawName) {
  if (!rawName) return [];
  const cands = new Set();
  const name = String(rawName);
  const parenRe = /[（(]([^）)]+)[）)]/g;
  let m;
  while ((m = parenRe.exec(name)) !== null) {
    const inner = m[1].trim();
    if (inner.length >= 2) cands.add(inner);
  }
  const outside = name.replace(/[（(][^）)]*[）)]/g, '').trim();
  if (outside.length >= 1) {
    const cleaned = outside
      .replace(/準?\d級[へにを]?/g, '')
      .replace(/さん[姉妹弟兄]?$/,'')
      .replace(/(弟|妹|兄|姉)$/,'')
      .trim();
    if (cleaned.length >= 1) cands.add(cleaned);
  }
  cands.add(name);
  return [...cands];
}

function extractSurname(raw) {
  const s = String(raw || '').replace(/[\s　]+/g, ' ').trim();
  const parts = s.split(' ');
  return parts[0] || '';
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

function matchPayer(payerRaw, amount) {
  const normPayer = normalizeName(payerRaw);
  if (!normPayer) return [];

  // 1. 学習済 payerNames で完全一致
  for (const [sid, payer] of Object.entries(STATE.overrides.payerNames || {})) {
    if (payer && normalizeName(payer) === normPayer) {
      const s = STATE.data.students.find(x => x.id === parseInt(sid, 10));
      if (s) return [{ studentId: s.id, name: s.name, score: 100, confidence: 'learned' }];
    }
  }

  const payerSurname = normalizeName(extractSurname(payerRaw));

  // 2. 全通塾生でマルチ候補スコア計算
  const cands = STATE.data.students
    .filter(s => s.status === '通塾')
    .map(s => {
      const nameCands = extractNameCandidates(s.name);
      let bestScore = 0;

      for (const cand of nameCands) {
        const norm = normalizeName(cand);
        if (!norm) continue;

        let score = 0;
        if (norm === normPayer) {
          score = 100;
        } else if (norm.includes(normPayer) || normPayer.includes(norm)) {
          score = 85;
        } else if (payerSurname.length >= 2) {
          if (norm.startsWith(payerSurname)) {
            score = 78;
          } else {
            const candSurname = normalizeName(extractSurname(cand));
            if (candSurname.length >= 2 && payerSurname === candSurname) score = 78;
          }
        }
        if (score === 0) {
          const common = lcs(norm, normPayer);
          if (common.length >= 2) score = Math.min(70, common.length * 18);
        }
        if (score > bestScore) bestScore = score;
      }

      if (bestScore > 0 && amount && s.fee && Math.abs(amount - s.fee) < 100) {
        bestScore = Math.min(100, bestScore + 8);
      }

      return bestScore > 0 ? { studentId: s.id, name: s.name, score: bestScore } : null;
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

// 前払い制: 入金月 → 翌月分として扱う (e.g. 2026-04 → 2026-05)
function nextMonth(ym) {
  if (!ym || !/^\d{4}-\d{2}$/.test(ym)) return ym;
  let [y, m] = ym.split('-').map(Number);
  m += 1;
  if (m > 12) { y += 1; m = 1; }
  return `${y}-${String(m).padStart(2, '0')}`;
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
    const matches = ignored ? [] : matchPayer(r.content, r.amount);
    const best = matches[0];
    return {
      idx: i,
      date: r.date,
      month: nextMonth(csvDateToMonth(r.date)),  // 前払い制: 入金月の翌月分
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
      const matches = matchPayer(c.payer, c.amount);
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
    const name = (file.name || '').toLowerCase();
    console.log('[handleFile] received:', { name: file.name, type: file.type, size: file.size });
    if (name.endsWith('.pdf') || file.type === 'application/pdf') {
      // PDF 取込 (2026-05-07 追加: 楽天銀行入出金明細 PDF 対応)
      console.log('[handleFile] PDF mode');
      const result = await extractPdfText(file);
      console.log('[handleFile] extractPdfText result:', { numPages: result?.numPages, textLen: result?.text?.length, head: result?.text?.slice(0, 200) });
      // text の長さで原因切り分け + 診断情報を alert に表示 (塾長スクショ送信用)
      if (!result || !result.text || result.text.length < 50) {
        const diag = result?.diag || 'no diag';
        const v = (typeof pdfjsLib !== 'undefined' ? (pdfjsLib.version || 'loaded') : 'NOT loaded');
        const ws = (typeof pdfjsLib !== 'undefined' ? (pdfjsLib.GlobalWorkerOptions?.workerSrc?.slice(-40) || 'no worker') : '-');
        let reason = '';
        if (result && result.numPages === 0) reason = '・PDF にページがありません (ファイル破損)';
        else if (result && result.text && result.text.length < 50) reason = '・テキストがほぼ抽出されていません';
        else reason = '・テキスト抽出が空 (= スキャン画像 PDF か pdf.js 互換問題の可能性)';
        alert(`PDF からテキストを取得できませんでした。\n\n${reason}\n\n📋 診断情報 (このスクショを送ってください):\n• pdf.js: ${v}\n• worker: ...${ws}\n• ${diag}\n\n対策候補:\n1. ブラウザを強制リロード (Cmd+Shift+R)\n2. 別ブラウザ (Chrome 推奨) で試す\n3. スクショを送って頂ければ詳細解析します`);
        return;
      }
      const rows = parsePDFText(result.text);
      if (!rows.length) {
        alert(`PDF から ${result.text.length}文字 のテキストは取れましたが、有効な取引行が見つかりませんでした。\n\n考えられる原因:\n• 楽天銀行「入出金明細」以外の PDF\n• フォーマット変更 (複数列レイアウト等)\n\n抽出テキストの先頭 100 文字:\n${result.text.slice(0, 100)}`);
        return;
      }
      processImport(rows);
      return;
    }
    // CSV 既存ロジック
    const text = await decodeFile(file);
    const rows = parseCSVText(text);
    if (!rows.length) { alert('CSVに有効な行が見つかりませんでした'); return; }
    processImport(rows);
  } catch (err) {
    console.error(err);
    alert('読込エラー: ' + err.message);
  }
}

// === PDF 取込 (2026-05-07 追加) ===========================================
// 楽天銀行「入出金明細」PDF を pdf.js で text 抽出 → CSV と同じ rows 形式に変換。
// PDF の text 構造は 4 行 1 set:
//   取引日 (YYYY/MM/DD) / 入出金 (±N,NNN) / 残高 (N,NNN) / 内容 (任意文字列)
async function extractPdfText(file) {
  if (typeof pdfjsLib === 'undefined') {
    throw new Error('pdf.js が読込まれていません。ページをリロードして再試行してください。');
  }
  // worker URL を設定 (CDN 同 version)
  if (!pdfjsLib.GlobalWorkerOptions.workerSrc) {
    pdfjsLib.GlobalWorkerOptions.workerSrc =
      'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
  }
  const buf = await file.arrayBuffer();
  const pdf = await pdfjsLib.getDocument({ data: buf }).promise;
  if (!pdf || !pdf.numPages) return { text: '', numPages: 0, diag: 'no pages' };
  const allLines = [];
  let totalItems = 0;
  const itemsPerPage = [];
  for (let p = 1; p <= pdf.numPages; p++) {
    const page = await pdf.getPage(p);
    const content = await page.getTextContent();
    // pdf.js getTextContent items は { str, transform: [a,b,c,d,e,f] } の配列。
    // f が y 座標 (PDF は左下原点なので y 大 → 上、y 小 → 下)。
    // 同一行 (= y がほぼ同じ) を結合 → y 降順で並べる で reading order に揃える。
    const items = content.items.filter(it => it && typeof it.str === 'string');
    totalItems += items.length;
    itemsPerPage.push(items.length);
    // 行ごとに group (y 座標で集約・誤差 2pt 以内は同行扱い)
    const lineMap = new Map();
    for (const it of items) {
      const y = Math.round((it.transform && it.transform[5]) || 0);
      // 2pt 以内の既存 y キーがあれば合流
      let key = y;
      for (const k of lineMap.keys()) { if (Math.abs(k - y) <= 2) { key = k; break; } }
      const x = (it.transform && it.transform[4]) || 0;
      const arr = lineMap.get(key) || [];
      arr.push({ x, str: it.str });
      lineMap.set(key, arr);
    }
    // y 降順 (= 上から下) で並べる
    const ys = [...lineMap.keys()].sort((a, b) => b - a);
    for (const y of ys) {
      const arr = lineMap.get(y).sort((a, b) => a.x - b.x);
      // x 差で空白挿入 (Reviewer A CRITICAL: 単純 join('') だと「振込 タナカ タロウ」→「振込タナカタロウ」と詰まり matchPayer が壊れる)
      let line = '';
      for (let k = 0; k < arr.length; k++) {
        const o = arr[k];
        if (k === 0) { line = o.str; continue; }
        const prev = arr[k - 1];
        const prevEnd = (prev.x || 0) + (prev.width || 0);
        const gap = (o.x || 0) - prevEnd;
        // 経験値 2pt 超で空白挿入。既に str の末尾/先頭に空白がある場合は重複させない。
        const sepNeeded = gap > 2 && !/\s$/.test(line) && !/^\s/.test(o.str);
        line += (sepNeeded ? ' ' : '') + o.str;
      }
      line = line.trim();
      if (line) allLines.push(line);
    }
  }
  const text = allLines.join('\n');
  const diag = `pages=${pdf.numPages}, totalItems=${totalItems}, perPage=[${itemsPerPage.join(',')}], lines=${allLines.length}, textLen=${text.length}, head100=${JSON.stringify(text.slice(0, 100))}`;
  console.log('[extractPdfText] diag:', diag);
  return { text, numPages: pdf.numPages, diag };
}

function parsePDFText(text) {
  const lines = text.split(/\r?\n/).map(l => l.trim()).filter(l => l);
  console.log('[parsePDFText] input lines:', lines.length);

  // === Strategy A: 4 行 1 set (pypdf 形式 / 列ごとに改行されるケース) ===
  const datePat = /^\d{4}\/\d{2}\/\d{2}$/;
  const numPat = /^[+-]?[\d,]+$/;
  const outA = [];
  let i = 0;
  while (i < lines.length) {
    if (!datePat.test(lines[i])) { i++; continue; }
    if (i + 3 >= lines.length) { i++; continue; }
    const dateStr = lines[i].replace(/\//g, '');
    const amountRaw = lines[i + 1];
    const balanceRaw = lines[i + 2];
    const content = lines[i + 3];
    if (!numPat.test(amountRaw) || !numPat.test(balanceRaw)) { i++; continue; }
    const amount = parseInt(amountRaw.replace(/[,+]/g, ''), 10);
    const balance = parseInt(balanceRaw.replace(/[,+]/g, ''), 10);
    if (isNaN(amount) || isNaN(balance)) { i++; continue; }
    outA.push({ date: dateStr, amount, balance, content });
    i += 4;
  }
  console.log('[parsePDFText] Strategy A (4-line set):', outA.length, 'rows');
  if (outA.length > 0) return outA;

  // === Strategy B: 1 行に 4 値 (pdf.js が同 y 座標を行に合体するケース) ===
  // 例: "2026/03/10 7,500 3,021,780 キタモト ヒカリ"
  // 例: "2026/03/10 -55,000 3,014,280 カ－ド出金 セブン銀行003401001109486"
  const lineRegex = /^(\d{4}\/\d{2}\/\d{2})\s+([+-]?[\d,]+)\s+([\d,]+)\s+(.+)$/;
  const outB = [];
  for (const line of lines) {
    const m = line.match(lineRegex);
    if (!m) continue;
    const dateStr = m[1].replace(/\//g, '');
    const amount = parseInt(m[2].replace(/[,+]/g, ''), 10);
    const balance = parseInt(m[3].replace(/,/g, ''), 10);
    const content = m[4].trim();
    if (isNaN(amount) || isNaN(balance)) continue;
    outB.push({ date: dateStr, amount, balance, content });
  }
  console.log('[parsePDFText] Strategy B (single-line):', outB.length, 'rows');
  if (outB.length > 0) return outB;

  // === Strategy C: より緩い行スキャン (どこかに日付があれば後ろから 3 値+内容を探す) ===
  // pdf.js が縦書き的に出した場合や、ヘッダ列幅違いに対するセーフティネット
  const outC = [];
  const looseDate = /(\d{4}\/\d{2}\/\d{2})/;
  for (let k = 0; k < lines.length; k++) {
    const dm = lines[k].match(looseDate);
    if (!dm) continue;
    // この行の日付以降をパース
    const after = lines[k].slice(lines[k].indexOf(dm[1]) + dm[1].length).trim();
    const tail = after.match(/^([+-]?[\d,]+)\s+([\d,]+)\s+(.+)$/);
    if (!tail) continue;
    const dateStr = dm[1].replace(/\//g, '');
    const amount = parseInt(tail[1].replace(/[,+]/g, ''), 10);
    const balance = parseInt(tail[2].replace(/,/g, ''), 10);
    const content = tail[3].trim();
    if (isNaN(amount) || isNaN(balance)) continue;
    outC.push({ date: dateStr, amount, balance, content });
  }
  console.log('[parsePDFText] Strategy C (loose):', outC.length, 'rows');
  return outC;
}

// === Stripe Charges API 取込 (CSV と同じ rows 形式に変換 → processImport で再利用) ===

function chargesToRows(charges) {
  return charges.map(c => {
    const d = new Date((c.created || 0) * 1000);
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const dd = String(d.getDate()).padStart(2, '0');
    const dateStr = `${yyyy}${mm}${dd}`;  // 楽天CSV と同じ YYYYMMDD 文字列形式に統一
    const payer = (c.customer_name || c.customer_email || c.receipt_email || c.description || '(Stripe決済)').trim();
    return {
      date: dateStr,
      amount: Number(c.amount) || 0,
      content: payer,
      _source: 'stripe',
      _stripeId: c.id,
    };
  });
}

async function importFromStripe() {
  const status = document.getElementById('stripeImportStatus');
  const btn = document.getElementById('stripeImportBtn');
  const month = STATE.currentMonth;
  if (!month || !/^\d{4}-\d{2}$/.test(month)) {
    status.innerHTML = '<span style="color:var(--error)">⚠ 対象月が選択されていません (画面上部の月セレクタで選んでください)</span>';
    return;
  }
  btn.disabled = true;
  status.textContent = '🔄 Stripe API から取得中...';
  try {
    const url = `/payment/api/stripe-charges?month=${encodeURIComponent(month)}`;
    const r = await fetch(url, { headers: { 'Accept': 'application/json' } });
    let data = null;
    try { data = await r.json(); } catch (e) { /* fallthrough: 非JSON応答 */ }
    if (!r.ok) {
      const isLocalhost = location.hostname === 'localhost' || location.hostname === '127.0.0.1' || location.hostname.startsWith('192.168.');
      const msg = (data && (data.message || data.error)) || `HTTP ${r.status}`;
      const hint = data && data.hint
        ? `<br><span style="color:var(--text-muted);font-size:0.82rem">${escapeHtml(data.hint)}</span>`
        : (r.status === 404 && isLocalhost
            ? '<br><span style="color:var(--text-muted);font-size:0.82rem">ℹ ローカル開発環境では Stripe 取込は動作しません。本番 (https://www.trillion-ai-juku.com/payment/) で試してください。</span>'
            : (r.status === 404
                ? '<br><span style="color:var(--text-muted);font-size:0.82rem">ℹ /payment/api/stripe-charges が見つかりません。Vercel への最新版デプロイをご確認ください。</span>'
                : ''));
      const link = data && data.dashboard ? `<br><a href="${escapeHtml(data.dashboard)}" target="_blank" style="color:var(--primary-light)">→ Vercel Dashboard を開く</a>` : '';
      status.innerHTML = `<span style="color:var(--error)">⚠ ${escapeHtml(msg)}</span>${hint}${link}`;
      return;
    }
    if (!data || data.count === 0) {
      status.innerHTML = `<span style="color:var(--text-muted)">✓ ${escapeHtml(month)} の Stripe 入金は 0 件でした (テスト環境キーの場合は本番キーに切替えてください)</span>`;
      return;
    }
    const rows = chargesToRows(data.charges);
    processImport(rows);
    status.innerHTML = `<span style="color:var(--success,#10b981)">✓ Stripe ${data.count} 件取込み完了。下の「要確認」リストでマッチを確認 → 「💾 確定して入金反映」を押してください</span>`;
  } catch (err) {
    console.error(err);
    const isLocalhost = location.hostname === 'localhost' || location.hostname === '127.0.0.1' || location.hostname.startsWith('192.168.');
    const localhostHint = isLocalhost
      ? '<br><span style="color:var(--text-muted);font-size:0.82rem">ローカル開発時は Stripe 取込は本番 (https://www.trillion-ai-juku.com/payment/) でのみ動作します</span>'
      : '';
    status.innerHTML = `<span style="color:var(--error)">⚠ 通信エラー: ${escapeHtml(err.message)}</span>${localhostHint}`;
  } finally {
    btn.disabled = false;
  }
}

// === 月初 Stripe 取込リマインダー (起動時自動表示) ===

const AUTO_IMPORT_KEY = 'juku-payment-auto-import-v1';

function getAutoImportRecord() {
  try { return JSON.parse(localStorage.getItem(AUTO_IMPORT_KEY) || '{}'); } catch (e) { return {}; }
}
function setAutoImportDone(month) {
  const rec = getAutoImportRecord();
  rec[month] = new Date().toISOString();
  localStorage.setItem(AUTO_IMPORT_KEY, JSON.stringify(rec));
}
function setAutoImportDismissed(month) {
  const rec = getAutoImportRecord();
  rec['dismissed_' + month] = true;
  localStorage.setItem(AUTO_IMPORT_KEY, JSON.stringify(rec));
}

function maybeShowAutoImportBanner() {
  const banner = document.getElementById('autoImportBanner');
  if (!banner) return;
  const today = new Date();
  // 月初 1〜10日のみリマインド
  if (today.getDate() > 10) { banner.classList.add('hidden'); return; }
  // 取込対象月 = 先月 (= currentMonth が今月の場合、先月の Stripe charges を取込→今月分 paid 反映: 前払い制)
  const target = (() => {
    const d = new Date(today.getFullYear(), today.getMonth() - 1, 1);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
  })();
  const rec = getAutoImportRecord();
  if (rec[target] || rec['dismissed_' + target]) { banner.classList.add('hidden'); return; }
  document.getElementById('autoImportTargetMonth').textContent = target;
  banner.dataset.targetMonth = target;
  banner.classList.remove('hidden');
}

async function runAutoImport() {
  const banner = document.getElementById('autoImportBanner');
  const target = banner?.dataset.targetMonth;
  if (!target) return;
  // CSV取込タブに遷移 + 月切替 + Stripe 取込実行
  switchTab('import');
  await new Promise(r => setTimeout(r, 100));
  // 月セレクタを取込対象月に切替
  STATE.currentMonth = target;
  document.getElementById('monthInput').value = target;
  const stripeMonthTag = document.getElementById('stripeMonthTag');
  if (stripeMonthTag) stripeMonthTag.textContent = target;
  const importMonthTag = document.getElementById('importMonthTag');
  if (importMonthTag) importMonthTag.textContent = `対象月: ${target}`;
  refresh();
  await new Promise(r => setTimeout(r, 200));
  await importFromStripe();
  setAutoImportDone(target);
  banner.classList.add('hidden');
}

function dismissAutoImport() {
  const banner = document.getElementById('autoImportBanner');
  const target = banner?.dataset.targetMonth;
  if (target) setAutoImportDismissed(target);
  banner.classList.add('hidden');
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

function buildStripeInviteFor(studentId) {
  const s = STATE.data.students.find(x => x.id === studentId);
  if (!s) return null;
  const vars = {
    student: s.name,
    juku: SETTINGS.jukuName,
    owner: SETTINGS.ownerName,
    ownerEmail: SETTINGS.ownerEmail,
    ownerPhone: SETTINGS.ownerPhone,
    fee: (s.fee || 0).toLocaleString('ja-JP'),
    deadlineDay: SETTINGS.deadlineDay || 25,
    paymentLink: paymentLinkFor(s),
    customerPortal: SETTINGS.stripeCustomerPortalUrl || '(Stripe Dashboard で Customer Portal を有効化してURLを設定モーダルに登録してください)',
  };
  return {
    student: s,
    to: getEmail(studentId),
    subject: renderTemplate(SETTINGS.stripeInviteSubject || DEFAULT_STRIPE_INVITE_SUBJECT, vars),
    body: renderTemplate(SETTINGS.stripeInviteBody || DEFAULT_STRIPE_INVITE_BODY, vars),
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

// === メアド一括登録 (CSV/TSV/改行区切り) ===

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function normalizeForMatch(s) {
  // 半角→全角統一、ひらがな→カタカナ等は不要、純粋に空白除去 + lower
  return String(s || '').replace(/[\s　]/g, '').toLowerCase();
}

function parseEmailImportInput(text) {
  const lines = String(text || '').split(/\r?\n/);
  const results = [];
  for (const raw of lines) {
    const line = raw.trim();
    if (!line) continue;
    // メアドを行末から検出 → 残りを ID/氏名 とする
    const tokens = line.split(/[,\t\s]+/).filter(Boolean);
    let email = null, key = null;
    for (let i = tokens.length - 1; i >= 0; i--) {
      if (EMAIL_RE.test(tokens[i])) {
        email = tokens[i];
        key = tokens.slice(0, i).join(' ').trim() || tokens.slice(i + 1).join(' ').trim();
        break;
      }
    }
    if (!email) {
      // メアドが見つからない行は parsing error として記録
      results.push({ raw: line, key: null, email: null, status: 'no_email' });
      continue;
    }
    if (!key) {
      results.push({ raw: line, key: null, email, status: 'no_key' });
      continue;
    }
    // ID マッチ (整数 or #整数)
    const idMatch = key.match(/^#?(\d+)$/);
    if (idMatch) {
      const id = parseInt(idMatch[1], 10);
      const s = STATE.data.students.find(x => x.id === id);
      if (s) {
        results.push({ raw: line, key, email, student: s, matchType: 'id', status: 'ok' });
        continue;
      }
      results.push({ raw: line, key, email, status: 'id_not_found' });
      continue;
    }
    // 氏名でマッチ: (1) 完全一致 (2) 部分一致 nameNorm.includes(keyNorm)
    const keyNorm = normalizeForMatch(key);
    const exact = STATE.data.students.filter(s => normalizeForMatch(s.name) === keyNorm);
    if (exact.length === 1) {
      results.push({ raw: line, key, email, student: exact[0], matchType: 'name_exact', status: 'ok' });
      continue;
    }
    if (exact.length > 1) {
      const active = exact.filter(s => (STATE.overrides.status?.[s.id] ?? s.status) === '通塾');
      if (active.length === 1) {
        results.push({ raw: line, key, email, student: active[0], matchType: 'name_exact_active', status: 'ok' });
      } else {
        results.push({ raw: line, key, email, candidates: exact, status: 'ambiguous' });
      }
      continue;
    }
    // 部分一致 (key が name の一部 or 通塾中で1名に絞れる場合)
    const partial = STATE.data.students.filter(s => normalizeForMatch(s.name).includes(keyNorm));
    if (partial.length === 1) {
      results.push({ raw: line, key, email, student: partial[0], matchType: 'name_partial', status: 'ok' });
    } else if (partial.length === 0) {
      results.push({ raw: line, key, email, status: 'name_not_found' });
    } else {
      const active = partial.filter(s => (STATE.overrides.status?.[s.id] ?? s.status) === '通塾');
      if (active.length === 1) {
        results.push({ raw: line, key, email, student: active[0], matchType: 'name_partial_active', status: 'ok' });
      } else {
        results.push({ raw: line, key, email, candidates: partial, status: 'ambiguous' });
      }
    }
  }
  return results;
}

function renderEmailImportPreview() {
  const text = document.getElementById('emailImportInput').value;
  const preview = document.getElementById('emailImportPreview');
  if (!text.trim()) { preview.innerHTML = ''; return; }
  const results = parseEmailImportInput(text);
  const ok = results.filter(r => r.status === 'ok');
  const fail = results.filter(r => r.status !== 'ok');
  const rows = results.map(r => {
    if (r.status === 'ok') {
      return `<div style="color:var(--success,#10b981)">✓ #${r.student.id} ${escapeHtml(r.student.name)} → ${escapeHtml(r.email)} <span style="color:var(--text-muted);font-size:0.75rem">[${r.matchType}]</span></div>`;
    }
    const reasons = {
      no_email: 'メアド形式の値が見つからない',
      no_key: 'ID/氏名が空',
      id_not_found: `ID「${r.key}」の生徒が見つからない`,
      name_not_found: `「${r.key}」と一致する生徒が見つからない`,
      ambiguous: `「${r.key}」は複数生徒に該当 (${r.candidates?.length}名) → ID 指定推奨`,
    };
    return `<div style="color:var(--warning)">⚠ ${escapeHtml(r.raw)} — ${escapeHtml(reasons[r.status] || r.status)}</div>`;
  }).join('');
  preview.innerHTML = `
    <div style="margin-bottom:0.5rem"><strong>解析結果</strong>: 成功 <span style="color:var(--success,#10b981)">${ok.length}件</span> / 失敗 <span style="color:var(--warning)">${fail.length}件</span></div>
    <div style="font-family:'SF Mono',Menlo,monospace;font-size:0.78rem;line-height:1.6">${rows}</div>
  `;
}

function applyEmailImport() {
  const text = document.getElementById('emailImportInput').value;
  if (!text.trim()) { alert('入力が空です'); return; }
  const results = parseEmailImportInput(text);
  const ok = results.filter(r => r.status === 'ok');
  const fail = results.filter(r => r.status !== 'ok');
  if (!ok.length) { alert('登録可能な行がありません。プレビューで失敗理由を確認してください。'); return; }
  const confirmMsg = `${ok.length}名分のメールアドレスを登録します。${fail.length ? `\n(${fail.length}件は解析失敗のためスキップ)` : ''}\n\n続行しますか？`;
  if (!confirm(confirmMsg)) return;
  ok.forEach(r => setEmail(r.student.id, r.email));
  alert(`✅ ${ok.length}名分のメアドを登録しました`);
  hideModal('emailImportModal');
  document.getElementById('emailImportInput').value = '';
  document.getElementById('emailImportPreview').innerHTML = '';
  refresh();
}

function openEmailImportModal() {
  document.getElementById('emailImportInput').value = '';
  document.getElementById('emailImportPreview').innerHTML = '';
  showModal('emailImportModal');
}

// === Stripe 案内メール一斉送信 (現通塾生にカード決済登録を促す) ===

function stripeInviteTargets(opts = {}) {
  const onlyUnsent = opts.onlyUnsent !== false;
  return activeStudents().filter(s => {
    if (!getEmail(s.id)) return false;
    if (!paymentLinkFor(s) || paymentLinkFor(s) === '(未設定)') return false;
    if (onlyUnsent && getStripeInviteSent(s.id)) return false;
    return true;
  });
}

function openStripeInviteModal() {
  const targetsAll = stripeInviteTargets({ onlyUnsent: false });
  const targetsUnsent = stripeInviteTargets({ onlyUnsent: true });
  const totalActive = activeStudents().length;
  const noEmail = activeStudents().filter(s => !getEmail(s.id)).length;
  const noLink = activeStudents().filter(s => {
    const link = paymentLinkFor(s);
    return getEmail(s.id) && (!link || link === '(未設定)');
  }).length;
  document.getElementById('stripeInviteSummary').innerHTML =
    `通塾生 <strong>${totalActive}名</strong> のうち:<br>` +
    `　・送信対象 (メアド+リンク有・未送信): <strong style="color:var(--success,#10b981)">${targetsUnsent.length}名</strong><br>` +
    `　・既に送信済 (再送可): <strong style="color:var(--text-muted)">${targetsAll.length - targetsUnsent.length}名</strong><br>` +
    `　・メアド未登録: <strong style="color:var(--warning)">${noEmail}名</strong> → 全生徒タブで登録してください<br>` +
    `　・Stripe Payment Link 未設定の月謝額: <strong style="color:var(--warning)">${noLink}名</strong> → 設定モーダルで登録してください`;
  showModal('stripeInviteModal');
}

function bulkStripeInviteSequential(opts = {}) {
  const targets = stripeInviteTargets({ onlyUnsent: opts.onlyUnsent !== false });
  if (!targets.length) { alert('送信対象がありません'); return; }
  hideModal('stripeInviteModal');
  if (!confirm(`${targets.length}名のメーラーを順次開きます。\nブラウザのポップアップブロックを解除してください。続行しますか？`)) return;
  let i = 0;
  const next = () => {
    if (i >= targets.length) { alert(`✅ ${targets.length}名分の Stripe 案内メーラーを開きました`); refresh(); return; }
    const s = targets[i];
    const m = buildStripeInviteFor(s.id);
    if (m && m.to) {
      if (mailtoSafetyCheck(m.to, m.subject, m.body)) {
        window.open(mailtoUrl(m.to, m.subject, m.body), '_blank');
        setStripeInviteSent(s.id, new Date().toISOString().slice(0, 10));
      }
    }
    i++;
    setTimeout(next, 800);
  };
  next();
}

function bulkStripeInviteBccCopy() {
  const targets = stripeInviteTargets({ onlyUnsent: false });
  if (!targets.length) { alert('送信対象がありません'); return; }
  const bcc = targets.map(s => getEmail(s.id)).join(', ');
  const vars = {
    student: '保護者各位',
    juku: SETTINGS.jukuName,
    owner: SETTINGS.ownerName,
    ownerEmail: SETTINGS.ownerEmail,
    ownerPhone: SETTINGS.ownerPhone,
    fee: '(各人別)',
    deadlineDay: SETTINGS.deadlineDay || 25,
    paymentLink: '(各人個別のURLを記載してください)',
    customerPortal: SETTINGS.stripeCustomerPortalUrl || '',
  };
  const subject = renderTemplate(SETTINGS.stripeInviteSubject || DEFAULT_STRIPE_INVITE_SUBJECT, vars);
  const body = renderTemplate(SETTINGS.stripeInviteBody || DEFAULT_STRIPE_INVITE_BODY, vars);
  const text = `BCC: ${bcc}\n\n件名: ${subject}\n\n${body}`;
  copyToClipboard(text);
  alert(`📋 ${targets.length}名分のBCC・件名・本文 (共通) をクリップボードにコピーしました\n\n※ paymentLink は各人別なので一括BCCには不向き。順次送信を推奨します。`);
  hideModal('stripeInviteModal');
}

function previewStripeInvite() {
  const targets = stripeInviteTargets({ onlyUnsent: false });
  if (!targets.length) { alert('プレビュー対象がいません (メアド+リンク登録済の通塾生が必要)'); return; }
  const m = buildStripeInviteFor(targets[0].id);
  if (!m) return;
  alert(`【プレビュー: ${m.student.name} 様】\n\n宛先: ${m.to}\n件名: ${m.subject}\n\n${m.body}`);
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

  tbody.onclick = async (e) => {
    const btn = e.target.closest('[data-invoice-id]');
    if (btn) {
      const id = parseInt(btn.dataset.invoiceId, 10);
      btn.disabled = true; const orig = btn.textContent; btn.textContent = '⏳ 生成中…';
      try { await generateInvoicePDF(id, /*download*/ true); }
      finally { btn.disabled = false; btn.textContent = orig; }
    }
  };
}

function getSelectedInvoiceIds() {
  return [...document.querySelectorAll('.invoice-check:checked')].map(c => parseInt(c.value, 10));
}

function buildInvoiceHTML(s, month) {
  const stripeUrl = paymentLinkFor(s);
  const customerPortal = SETTINGS.stripeCustomerPortalUrl || '';
  const today = new Date().toISOString().slice(0, 10);
  const due = deadlineForMonth(month);
  const courses = (s.courses || []).join(' / ') || '—';
  const fee = (s.fee || 0).toLocaleString('ja-JP');
  const note = s.notes ? `<div class="note-line">※ ${escapeHtml(s.notes)}</div>` : '';

  // HTML 生成 (html2canvas で画像化する用、A4 比率)
  return `
  <div style="width:794px; padding:48px 56px; background:#fff; color:#1f2937; font-family:'Noto Sans JP','Hiragino Sans','Yu Gothic UI',-apple-system,sans-serif; font-size:14px; line-height:1.5;">
    <div style="display:flex; justify-content:space-between; align-items:start; margin-bottom:32px;">
      <div>
        <div style="font-size:32px; font-weight:800; color:#111827; letter-spacing:-0.5px;">請求書</div>
        <div style="font-size:13px; color:#6b7280; margin-top:4px;">INVOICE</div>
      </div>
      <div style="text-align:right; font-size:13px; color:#374151;">
        <div>請求書 No. <strong>${month}-${String(s.id).padStart(4,'0')}</strong></div>
        <div style="margin-top:2px;">発行日: ${today}</div>
        <div style="margin-top:2px;">支払期限: <strong style="color:#dc2626;">${escapeHtml(due)}</strong></div>
      </div>
    </div>

    <div style="background:linear-gradient(135deg,#6366f1,#818cf8); color:#fff; padding:14px 20px; border-radius:10px 10px 0 0; font-weight:700; font-size:15px;">
      ご請求先
    </div>
    <table style="width:100%; border-collapse:collapse; margin-bottom:24px;">
      <tbody>
        <tr><td style="padding:12px 18px; border:1px solid #e5e7eb; background:#f9fafb; font-weight:600; width:30%;">生徒氏名</td><td style="padding:12px 18px; border:1px solid #e5e7eb;">${escapeHtml(s.name)}</td></tr>
        <tr><td style="padding:12px 18px; border:1px solid #e5e7eb; background:#f9fafb; font-weight:600;">学年</td><td style="padding:12px 18px; border:1px solid #e5e7eb;">${escapeHtml(s.grade || '—')}</td></tr>
        <tr><td style="padding:12px 18px; border:1px solid #e5e7eb; background:#f9fafb; font-weight:600;">受講コース</td><td style="padding:12px 18px; border:1px solid #e5e7eb;">${escapeHtml(courses)}</td></tr>
        <tr><td style="padding:12px 18px; border:1px solid #e5e7eb; background:#f9fafb; font-weight:600;">対象月</td><td style="padding:12px 18px; border:1px solid #e5e7eb;">${month}</td></tr>
        <tr><td style="padding:12px 18px; border:1px solid #e5e7eb; background:#f9fafb; font-weight:600;">請求金額</td><td style="padding:12px 18px; border:1px solid #e5e7eb; font-size:20px; font-weight:800; color:#6366f1;">¥${fee}</td></tr>
      </tbody>
    </table>
    ${note}

    <div style="background:linear-gradient(135deg,#ec4899,#f472b6); color:#fff; padding:14px 20px; border-radius:10px 10px 0 0; font-weight:700; font-size:15px; margin-top:24px;">
      お支払い方法 1. 銀行振込
    </div>
    <table style="width:100%; border-collapse:collapse; margin-bottom:24px;">
      <tbody>
        <tr><td style="padding:11px 18px; border:1px solid #e5e7eb; background:#fdf2f8; font-weight:600; width:30%;">銀行名</td><td style="padding:11px 18px; border:1px solid #e5e7eb;">${escapeHtml(SETTINGS.bankName || '—')}</td></tr>
        <tr><td style="padding:11px 18px; border:1px solid #e5e7eb; background:#fdf2f8; font-weight:600;">支店名</td><td style="padding:11px 18px; border:1px solid #e5e7eb;">${escapeHtml(SETTINGS.branchName || '—')}</td></tr>
        <tr><td style="padding:11px 18px; border:1px solid #e5e7eb; background:#fdf2f8; font-weight:600;">口座種別</td><td style="padding:11px 18px; border:1px solid #e5e7eb;">${escapeHtml(SETTINGS.accountType || '普通')}</td></tr>
        <tr><td style="padding:11px 18px; border:1px solid #e5e7eb; background:#fdf2f8; font-weight:600;">口座番号</td><td style="padding:11px 18px; border:1px solid #e5e7eb; font-family:'Menlo',monospace; letter-spacing:1px;">${escapeHtml(SETTINGS.accountNumber || '—')}</td></tr>
        <tr><td style="padding:11px 18px; border:1px solid #e5e7eb; background:#fdf2f8; font-weight:600;">口座名義</td><td style="padding:11px 18px; border:1px solid #e5e7eb;">${escapeHtml(SETTINGS.accountHolder || '—')}</td></tr>
      </tbody>
    </table>

    ${stripeUrl && stripeUrl !== '(未設定)' ? `
    <div style="background:linear-gradient(135deg,#10b981,#34d399); color:#fff; padding:14px 20px; border-radius:10px 10px 0 0; font-weight:700; font-size:15px;">
      お支払い方法 2. クレジットカード (Stripe)
    </div>
    <table style="width:100%; border-collapse:collapse; margin-bottom:18px;">
      <tbody>
        <tr><td style="padding:11px 18px; border:1px solid #e5e7eb; background:#ecfdf5; font-weight:600; width:30%;">支払いリンク</td><td style="padding:11px 18px; border:1px solid #e5e7eb; word-break:break-all; font-size:12px; color:#059669;">${escapeHtml(stripeUrl)}</td></tr>
        <tr><td style="padding:11px 18px; border:1px solid #e5e7eb; background:#ecfdf5; font-weight:600;">使い方</td><td style="padding:11px 18px; border:1px solid #e5e7eb;">URL にアクセス → カード情報入力 → 月額自動引き落としが開始されます</td></tr>
        ${customerPortal ? `<tr><td style="padding:11px 18px; border:1px solid #e5e7eb; background:#ecfdf5; font-weight:600;">変更・解約</td><td style="padding:11px 18px; border:1px solid #e5e7eb; word-break:break-all; font-size:12px; color:#059669;">${escapeHtml(customerPortal)}</td></tr>` : ''}
      </tbody>
    </table>
    ` : ''}

    <div style="display:flex; justify-content:flex-end; align-items:baseline; gap:18px; padding:18px 22px; background:linear-gradient(135deg,#1f2937,#374151); color:#fff; border-radius:12px; margin-top:8px;">
      <div style="font-size:14px; opacity:0.8;">合計</div>
      <div style="font-size:32px; font-weight:800; letter-spacing:-1px;">¥${fee}</div>
    </div>

    <div style="margin-top:36px; padding-top:18px; border-top:1px solid #e5e7eb; font-size:12px; color:#6b7280; line-height:1.7;">
      <div style="font-weight:600; color:#374151; margin-bottom:4px;">${escapeHtml(SETTINGS.jukuName || 'AI学習コーチ塾')}</div>
      ${SETTINGS.ownerName ? `<div>塾長: ${escapeHtml(SETTINGS.ownerName)}</div>` : ''}
      ${SETTINGS.ownerEmail ? `<div>📧 ${escapeHtml(SETTINGS.ownerEmail)}</div>` : ''}
      ${SETTINGS.ownerPhone ? `<div>📞 ${escapeHtml(SETTINGS.ownerPhone)}</div>` : ''}
      <div style="margin-top:8px; font-size:11px; color:#9ca3af;">ご不明点は塾長 LINE までお問い合わせください。</div>
    </div>
  </div>`;
}

async function generateInvoicePDF(studentId, download = true, returnDoc = false) {
  const s = STATE.data.students.find(x => x.id === studentId);
  if (!s) return null;
  const month = STATE.currentMonth;

  // 1. HTML を一時的に DOM に追加 (画面外、html2canvas で画像化する用)
  const container = document.createElement('div');
  container.style.cssText = 'position:fixed; left:-10000px; top:0; pointer-events:none; opacity:1;';
  container.innerHTML = buildInvoiceHTML(s, month);
  document.body.appendChild(container);
  // フォント描画完了を待つ (Noto Sans JP の load 確実化)
  if (document.fonts && document.fonts.ready) {
    try { await document.fonts.ready; } catch (e) {}
  }

  try {
    // 2. html2canvas で画像化 (高 DPI = 2x で文字滑らか)
    const canvas = await html2canvas(container.firstElementChild, {
      scale: 2,
      backgroundColor: '#ffffff',
      logging: false,
      useCORS: true,
    });
    // 3. jsPDF にイメージ埋込み (A4 サイズに収める)
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF({ unit: 'mm', format: 'a4', compress: true });
    const pageW = 210;
    const pageH = 297;
    const imgW = pageW - 20;  // 左右 10mm マージン
    const imgH = (canvas.height / canvas.width) * imgW;
    const imgData = canvas.toDataURL('image/jpeg', 0.92);

    if (imgH <= pageH - 20) {
      doc.addImage(imgData, 'JPEG', 10, 10, imgW, imgH, undefined, 'FAST');
    } else {
      // 縦長で 1 ページに収まらない場合は分割描画
      const pageImgH = pageH - 20;
      const totalPages = Math.ceil(imgH / pageImgH);
      for (let p = 0; p < totalPages; p++) {
        if (p > 0) doc.addPage();
        const yOffset = -p * pageImgH;
        doc.addImage(imgData, 'JPEG', 10, 10 + yOffset, imgW, imgH, undefined, 'FAST');
      }
    }

    if (returnDoc) { document.body.removeChild(container); return doc; }
    if (download) {
      const safeName = (s.name || '').replace(/[\\/:*?"<>|]/g, '_').slice(0, 20);
      const filename = `請求書_${month}_${s.id}_${safeName}.pdf`;
      doc.save(filename);
    }
    document.body.removeChild(container);
    return doc;
  } catch (e) {
    document.body.removeChild(container);
    console.error('PDF generation failed:', e);
    alert('PDF 生成に失敗しました: ' + (e.message || e));
    return null;
  }
}

async function bulkInvoicePDF() {
  const ids = getSelectedInvoiceIds();
  if (!ids.length) { alert('対象を選択してください'); return; }
  if (ids.length > 100 && !confirm(`${ids.length}名分を生成します。時間がかかります。続行しますか？`)) return;

  const zip = new JSZip();
  const month = STATE.currentMonth;
  let success = 0;
  for (const id of ids) {
    const doc = await generateInvoicePDF(id, false, true);
    if (doc) {
      const s = STATE.data.students.find(x => x.id === id);
      const safe = (s?.name || '').replace(/[\\/:*?"<>|]/g, '_').slice(0, 20);
      const filename = `請求書_${month}_${id}_${safe}.pdf`;
      zip.file(filename, doc.output('blob'));
      success++;
    }
  }
  const blob = await zip.generateAsync({ type: 'blob' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = `invoices_${month}.zip`;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  alert(`✅ ${success}/${ids.length}件の請求書PDFを ZIP でダウンロードしました`);
}

async function previewInvoicePDF() {
  const ids = getSelectedInvoiceIds();
  const id = ids[0] || activeStudents()[0]?.id;
  if (!id) { alert('対象を選択してください'); return; }
  const doc = await generateInvoicePDF(id, false, true);
  if (!doc) return;
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

// === 連絡センター (Communication: 一斉/個別/履歴) ===

const COMM_STATE = {
  subTab: 'broadcast',          // 'broadcast'|'individual'|'history'
  selectedStudentId: null,      // 個別送信用
};

function getCommHistory() {
  return STATE.overrides.commHistory || [];
}
function appendCommHistory(entry) {
  if (!STATE.overrides.commHistory) STATE.overrides.commHistory = [];
  STATE.overrides.commHistory.unshift({
    ...entry,
    sentAt: new Date().toISOString(),
  });
  // 最大 500 件で trim
  if (STATE.overrides.commHistory.length > 500) {
    STATE.overrides.commHistory = STATE.overrides.commHistory.slice(0, 500);
  }
  saveOverrides();
}

// CRLF/制御文字注入対策 (件名 = ヘッダ位置で危険)
function sanitizeSubject(s) {
  return String(s || '').replace(/[\r\n\t\x00-\x1F]/g, ' ').trim().slice(0, 200);
}

function commFilteredTargets() {
  const status = document.getElementById('commFilterStatus')?.value ?? '通塾';
  const grade = document.getElementById('commFilterGrade')?.value || '';
  const course = document.getElementById('commFilterCourse')?.value || '';
  const unpaid = document.getElementById('commFilterUnpaid')?.value || '';
  const month = STATE.currentMonth;
  return STATE.data.students.filter(s => {
    const st = STATE.overrides.status?.[s.id] ?? s.status;
    if (status && st !== status) return false;
    if (grade && s.grade !== grade) return false;
    if (course && !(s.courses || []).includes(course)) return false;
    if (unpaid === 'unpaid') {
      const p = getPayment(month, s.id);
      if (p && p.paid) return false;
    } else if (unpaid === 'paid') {
      const p = getPayment(month, s.id);
      if (!p || !p.paid) return false;
    }
    return true;
  });
}

function renderCommunication() {
  // フィルタ プルダウン populate
  const grades = uniqueGrades();
  const courses = uniqueCourses();
  const gradeSel = document.getElementById('commFilterGrade');
  const courseSel = document.getElementById('commFilterCourse');
  if (gradeSel && gradeSel.children.length <= 1) {
    grades.forEach(g => {
      const o = document.createElement('option');
      o.value = g; o.textContent = g; gradeSel.appendChild(o);
    });
  }
  if (courseSel && courseSel.children.length <= 1) {
    courses.forEach(c => {
      const o = document.createElement('option');
      o.value = c; o.textContent = c; courseSel.appendChild(o);
    });
  }
  // 通塾生数
  const activeCnt = activeStudents().length;
  const tag = document.getElementById('commActiveCountTag');
  if (tag) tag.textContent = `通塾 ${activeCnt}名`;
  // 各サブタブ初期描画
  renderCommBroadcastPreview();
  renderCommIndividualList();
  renderCommHistory();
  // テンプレ初期値 (空なら督促テンプレ流用)
  const subj = document.getElementById('commBroadcastSubject');
  const body = document.getElementById('commBroadcastBody');
  if (subj && !subj.value) subj.value = SETTINGS.commBroadcastSubject || '【{{juku}}】お知らせ';
  if (body && !body.value) body.value = SETTINGS.commBroadcastBody || `{{student}} 様の保護者様

いつも{{juku}}をご利用いただきありがとうございます。

(ここに本文を入力してください)

────────────────────
{{juku}}
{{owner}}
{{ownerEmail}}
{{ownerPhone}}
────────────────────`;
}

function switchCommSub(name) {
  COMM_STATE.subTab = name;
  document.querySelectorAll('[data-comm-tab]').forEach(t => {
    t.classList.toggle('match-tab-active', t.dataset.commTab === name);
  });
  document.querySelectorAll('[data-comm-sub]').forEach(p => {
    p.classList.toggle('hidden', p.dataset.commSub !== name);
  });
  if (name === 'history') renderCommHistory();
  if (name === 'individual') renderCommIndividualList();
  if (name === 'broadcast') renderCommBroadcastPreview();
}

function renderCommBroadcastPreview() {
  const targets = commFilteredTargets();
  const withEmail = targets.filter(s => getEmail(s.id));
  const noEmail = targets.length - withEmail.length;
  const sample = withEmail.slice(0, 5).map(s => escapeHtml(s.name)).join(', ');
  const previewEl = document.getElementById('commTargetPreview');
  if (!previewEl) return;
  previewEl.innerHTML = `
    <strong>送信対象</strong>: <span style="color:var(--success,#10b981);font-weight:700">${withEmail.length}名</span>
    ${noEmail > 0 ? `<span style="color:var(--warning);margin-left:0.6rem">(メアド未登録 ${noEmail}名はスキップ)</span>` : ''}
    ${sample ? `<br><span style="color:var(--text-muted);font-size:0.82rem">先頭: ${sample}${withEmail.length > 5 ? ' …' : ''}</span>` : ''}
  `;
}

function buildBroadcastFor(studentId, subjectTpl, bodyTpl) {
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
    customerPortal: SETTINGS.stripeCustomerPortalUrl || '',
  };
  return {
    student: s,
    to: getEmail(studentId),
    subject: sanitizeSubject(renderTemplate(subjectTpl, vars)),
    body: renderTemplate(bodyTpl, vars),
  };
}

function commBroadcastPreview() {
  const subjectTpl = document.getElementById('commBroadcastSubject').value;
  const bodyTpl = document.getElementById('commBroadcastBody').value;
  const targets = commFilteredTargets().filter(s => getEmail(s.id));
  if (!targets.length) { alert('送信対象がいません (フィルタ条件 or メアド未登録)'); return; }
  const m = buildBroadcastFor(targets[0].id, subjectTpl, bodyTpl);
  if (!m) return;
  alert(`【プレビュー: ${m.student.name} 様】\n\n宛先: ${m.to}\n件名: ${m.subject}\n\n${m.body}`);
}

function commBroadcastSendSequential() {
  const subjectTpl = document.getElementById('commBroadcastSubject').value;
  const bodyTpl = document.getElementById('commBroadcastBody').value;
  if (!subjectTpl.trim() || !bodyTpl.trim()) { alert('件名と本文を入力してください'); return; }
  const targets = commFilteredTargets().filter(s => getEmail(s.id));
  if (!targets.length) { alert('送信対象がいません'); return; }
  if (!confirm(`${targets.length}名のメーラーを順次開きます (800ms間隔)。\nブラウザのポップアップブロックを解除してください。続行しますか？`)) return;
  let i = 0;
  let succeeded = 0;
  const next = () => {
    if (i >= targets.length) {
      appendCommHistory({
        type: 'broadcast',
        method: 'mailto_sequential',
        subject: sanitizeSubject(subjectTpl),
        bodyTpl,
        recipients: targets.map(s => ({ id: s.id, name: s.name, email: getEmail(s.id) })),
        recipientCount: succeeded,
      });
      alert(`✅ ${succeeded}/${targets.length} 名分のメーラーを開きました\n送信履歴に記録されました`);
      switchCommSub('history');
      return;
    }
    const s = targets[i];
    const m = buildBroadcastFor(s.id, subjectTpl, bodyTpl);
    if (m && m.to && mailtoSafetyCheck(m.to, m.subject, m.body)) {
      window.open(mailtoUrl(m.to, m.subject, m.body), '_blank');
      succeeded++;
    }
    i++;
    setTimeout(next, 800);
  };
  next();
}

async function commBroadcastSendResend() {
  // CHAT_ADMIN_PASSWORD を再利用 (chat と同じ管理者認証)
  const pw = (CHAT_STATE && CHAT_STATE.pw) || localStorage.getItem(CHAT_PW_KEY) || '';
  if (!pw) {
    if (!confirm('Resend 直送には管理パスワードが必要です。\n\n💬 チャットタブを開いて管理パスワードを入力 → 戻ってきて再度送信してください。\n\nチャットタブに移動しますか?')) return;
    switchTab('chat');
    return;
  }
  const subjectTpl = document.getElementById('commBroadcastSubject').value;
  const bodyTpl = document.getElementById('commBroadcastBody').value;
  if (!subjectTpl.trim() || !bodyTpl.trim()) { alert('件名と本文を入力してください'); return; }
  const targets = commFilteredTargets().filter(s => getEmail(s.id));
  if (!targets.length) { alert('送信対象がいません (フィルタ条件 or メアド未登録)'); return; }
  if (!confirm(`Resend API 経由で ${targets.length}名 に直接メール送信します。\n\n✓ Mac メーラー起動なし\n✓ BCC 漏れ事故ゼロ (1通ずつ to で送信)\n✓ サーバ側で送信\n\n送信元: ${SETTINGS.jukuName || ''} <info@trillion-ai-juku.com>\n\n続行しますか？`)) return;

  // recipients を構築 (テンプレ変数も per-student で渡す)
  const recipients = targets.map(s => ({
    email: getEmail(s.id),
    name: s.name,
    vars: {
      student: s.name,
      juku: SETTINGS.jukuName,
      owner: SETTINGS.ownerName,
      ownerEmail: SETTINGS.ownerEmail,
      ownerPhone: SETTINGS.ownerPhone,
      month: STATE.currentMonth,
      fee: (s.fee || 0).toLocaleString('ja-JP'),
      deadline: deadlineForMonth(STATE.currentMonth),
      bank: bankInfoText().split('　').join('\n'),
      paymentLink: paymentLinkFor(s),
      customerPortal: SETTINGS.stripeCustomerPortalUrl || '',
    },
  }));

  const btn = document.getElementById('commBroadcastResendBtn');
  const originalText = btn?.textContent;
  if (btn) { btn.disabled = true; btn.textContent = '📤 送信中...'; }

  try {
    const r = await fetch('/payment/api/mail-send', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Admin-Password': pw,
      },
      body: JSON.stringify({
        type: 'broadcast',
        subject: subjectTpl,
        body: bodyTpl,
        from_name: SETTINGS.jukuName || '',
        reply_to: SETTINGS.ownerEmail || '',
        recipients,
      }),
    });
    const data = await r.json();
    if (!r.ok) {
      if (r.status === 401) {
        alert(`⚠ 認証失敗。チャットタブで管理パスワード再設定してください。`);
      } else if (r.status === 503) {
        alert(`⚠ Resend API キーが Vercel に未設定です。\n${data.hint || ''}`);
      } else {
        alert(`⚠ ${data.message || data.error || r.status}`);
      }
      return;
    }
    appendCommHistory({
      type: 'broadcast',
      method: 'resend_api',
      subject: sanitizeSubject(subjectTpl),
      bodyTpl,
      recipients: targets.map(s => ({ id: s.id, name: s.name, email: getEmail(s.id) })),
      recipientCount: data.sent,
      failed: data.failed,
    });
    let msg = `✅ Resend 直送完了\n\n成功: ${data.sent}名\n失敗: ${data.failed}名`;
    if (data.failed > 0) {
      const failedList = data.results.filter(x => !x.ok).slice(0, 5).map(x => `  ・${x.email}: ${x.error || ''}`).join('\n');
      msg += `\n\n失敗詳細 (先頭5件):\n${failedList}`;
    }
    alert(msg);
    switchCommSub('history');
  } catch (e) {
    alert('通信エラー: ' + e.message);
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = originalText; }
  }
}

async function commIndividualSendResend(s, subject, body) {
  const pw = (CHAT_STATE && CHAT_STATE.pw) || localStorage.getItem(CHAT_PW_KEY) || '';
  if (!pw) { return null; }  // フォールバック (mailto に流す用)
  const r = await fetch('/payment/api/mail-send', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Admin-Password': pw,
    },
    body: JSON.stringify({
      type: 'individual',
      subject,
      body,
      from_name: SETTINGS.jukuName || '',
      reply_to: SETTINGS.ownerEmail || '',
      recipients: [{
        email: getEmail(s.id),
        name: s.name,
        vars: {},  // 既に展開済の subject/body が渡されてくる
      }],
    }),
  });
  return r.ok ? await r.json() : null;
}

function commBroadcastBccCopy() {
  const subjectTpl = document.getElementById('commBroadcastSubject').value;
  const bodyTpl = document.getElementById('commBroadcastBody').value;
  if (!subjectTpl.trim() || !bodyTpl.trim()) { alert('件名と本文を入力してください'); return; }
  const targets = commFilteredTargets().filter(s => getEmail(s.id));
  if (!targets.length) { alert('送信対象がいません'); return; }
  // 共通テンプレ展開 (生徒名は「保護者各位」)
  const genericVars = {
    student: '保護者各位',
    juku: SETTINGS.jukuName, owner: SETTINGS.ownerName,
    ownerEmail: SETTINGS.ownerEmail, ownerPhone: SETTINGS.ownerPhone,
    month: STATE.currentMonth,
    fee: '(各人別)',
    deadline: deadlineForMonth(STATE.currentMonth),
    bank: bankInfoText().split('　').join('\n'),
    paymentLink: '(各人個別の URL を記載してください)',
    customerPortal: SETTINGS.stripeCustomerPortalUrl || '',
  };
  const subject = sanitizeSubject(renderTemplate(subjectTpl, genericVars));
  const body = renderTemplate(bodyTpl, genericVars);
  const bcc = targets.map(s => getEmail(s.id)).join(', ');
  const text = `BCC: ${bcc}\n\n件名: ${subject}\n\n${body}`;
  copyToClipboard(text);
  appendCommHistory({
    type: 'broadcast',
    method: 'bcc_copy',
    subject,
    bodyTpl,
    recipients: targets.map(s => ({ id: s.id, name: s.name, email: getEmail(s.id) })),
    recipientCount: targets.length,
  });
  alert(`📋 ${targets.length}名分のBCC・件名・本文をクリップボードにコピーしました\n\nGmail等の新規メール作成画面に貼付けてください。`);
  switchCommSub('history');
}

function commBroadcastSaveTemplate() {
  SETTINGS.commBroadcastSubject = document.getElementById('commBroadcastSubject').value;
  SETTINGS.commBroadcastBody = document.getElementById('commBroadcastBody').value;
  saveSettings();
  alert('✅ 一斉送信テンプレを保存しました (件名+本文)');
}

function commBroadcastLoadTemplate() {
  document.getElementById('commBroadcastSubject').value = SETTINGS.commBroadcastSubject || '【{{juku}}】お知らせ';
  document.getElementById('commBroadcastBody').value = SETTINGS.commBroadcastBody || '';
  alert('📂 保存済テンプレを呼び出しました');
}

// ===== 個別送信 =====

function renderCommIndividualList() {
  const q = document.getElementById('commIndividualSearch')?.value?.trim().toLowerCase() || '';
  const list = document.getElementById('commIndividualList');
  if (!list) return;
  const candidates = activeStudents().filter(s => {
    if (!q) return true;
    return s.name.toLowerCase().includes(q) || (s.grade || '').toLowerCase().includes(q);
  }).slice(0, 200);
  list.innerHTML = candidates.map(s => {
    const email = getEmail(s.id);
    const sel = COMM_STATE.selectedStudentId === s.id ? 'background:rgba(99,102,241,0.2);border:1px solid rgba(99,102,241,0.5)' : 'background:rgba(255,255,255,0.03);border:1px solid transparent';
    return `
      <div class="comm-stu-row" data-stu-id="${s.id}" style="padding:0.6rem 0.8rem;margin-bottom:0.3rem;border-radius:8px;cursor:pointer;${sel}">
        <div style="display:flex;justify-content:space-between;align-items:baseline;gap:0.5rem">
          <div style="font-weight:600;font-size:0.9rem">${escapeHtml(s.name)}</div>
          <div style="font-size:0.75rem;color:var(--text-muted)">${escapeHtml(s.grade || '')}</div>
        </div>
        <div style="font-size:0.75rem;color:${email ? 'var(--text-muted)' : 'var(--warning)'};margin-top:0.2rem">${email ? escapeHtml(email) : '✗ メアド未登録'}</div>
      </div>
    `;
  }).join('');
  list.onclick = (e) => {
    const row = e.target.closest('.comm-stu-row');
    if (!row) return;
    COMM_STATE.selectedStudentId = parseInt(row.dataset.stuId, 10);
    renderCommIndividualList();
    renderCommIndividualEditor();
  };
}

function renderCommIndividualEditor() {
  const editor = document.getElementById('commIndividualEditor');
  if (!editor) return;
  const id = COMM_STATE.selectedStudentId;
  if (!id) {
    editor.innerHTML = `<div style="text-align:center;color:var(--text-muted);padding:3rem 0">← 左から生徒を選択してください</div>`;
    return;
  }
  const s = STATE.data.students.find(x => x.id === id);
  if (!s) return;
  const email = getEmail(id);
  const history = getCommHistory().filter(h => {
    if (h.type === 'individual') return h.studentId === id;
    if (h.type === 'broadcast') return (h.recipients || []).some(r => r.id === id);
    return false;
  }).slice(0, 30);
  editor.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:0.8rem;border-bottom:1px solid var(--border);padding-bottom:0.6rem">
      <div>
        <div style="font-size:1.1rem;font-weight:700">${escapeHtml(s.name)}</div>
        <div style="font-size:0.82rem;color:var(--text-muted)">${escapeHtml(s.grade || '')} / ${escapeHtml((s.courses||[]).join(', ') || '(コースなし)')}</div>
        <div style="font-size:0.82rem;color:${email ? 'var(--success,#10b981)' : 'var(--warning)'};margin-top:0.2rem">${email ? '✉ ' + escapeHtml(email) : '⚠ メアド未登録 — 全生徒タブで登録してください'}</div>
      </div>
      <div style="font-size:0.82rem;color:var(--text-muted);text-align:right">月謝 ¥${(s.fee || 0).toLocaleString('ja-JP')}<br>当月: ${getPayment(STATE.currentMonth, id)?.paid ? '✓ 入金済' : '✗ 未払'}</div>
    </div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.8rem;align-items:start">
      <div>
        <label class="form-group form-group-wide">
          <span>件名</span>
          <input type="text" id="commIndSubject" placeholder="件名を入力">
        </label>
        <label class="form-group form-group-wide">
          <span>本文 (Cmd+Enter で送信)</span>
          <textarea id="commIndBody" rows="14" placeholder="本文を入力..."></textarea>
        </label>
        <div style="display:flex;gap:0.5rem;flex-wrap:wrap;margin-top:0.5rem">
          <button class="btn btn-ghost btn-sm" id="commIndDunningTplBtn">📝 督促テンプレ</button>
          <button class="btn btn-ghost btn-sm" id="commIndStripeTplBtn">💳 Stripe案内テンプレ</button>
          <button class="btn btn-ghost btn-sm" id="commIndChatInviteBtn">💬 チャット招待 URL</button>
          <button class="btn btn-ghost btn-sm" id="commIndPreviewBtn">👁 プレビュー</button>
          <span style="flex:1"></span>
          <button class="btn btn-primary btn-sm" id="commIndSendBtn" ${email ? '' : 'disabled'}>📤 送信</button>
        </div>
      </div>
      <div>
        <h4 style="margin:0 0 0.5rem 0">📜 送信履歴 (${history.length})</h4>
        <div style="max-height:500px;overflow-y:auto;font-size:0.82rem">
          ${history.length === 0 ? '<div style="color:var(--text-muted);padding:1rem;text-align:center">履歴なし</div>' :
            history.map(h => `
              <div style="padding:0.5rem;margin-bottom:0.3rem;background:rgba(255,255,255,0.03);border-radius:6px;border-left:3px solid ${h.type === 'broadcast' ? 'var(--accent)' : 'var(--primary)'}">
                <div style="font-weight:600">${escapeHtml(h.subject || '(件名なし)')}</div>
                <div style="color:var(--text-muted);font-size:0.75rem;margin-top:0.2rem">${h.type === 'broadcast' ? `📢 一斉 (${h.recipientCount}名)` : '📨 個別'} · ${new Date(h.sentAt).toLocaleString('ja-JP')}</div>
              </div>
            `).join('')}
        </div>
      </div>
    </div>
  `;

  // 各ボタン bind
  document.getElementById('commIndPreviewBtn')?.addEventListener('click', () => {
    const subj = sanitizeSubject(document.getElementById('commIndSubject').value);
    const body = document.getElementById('commIndBody').value;
    alert(`【プレビュー】\n\n宛先: ${email || '(未登録)'}\n件名: ${subj}\n\n${body}`);
  });
  document.getElementById('commIndSendBtn')?.addEventListener('click', () => commIndividualSend());
  document.getElementById('commIndDunningTplBtn')?.addEventListener('click', () => loadIndividualTemplate('dunning'));
  document.getElementById('commIndStripeTplBtn')?.addEventListener('click', () => loadIndividualTemplate('stripe_invite'));
  document.getElementById('commIndChatInviteBtn')?.addEventListener('click', copyChatInviteForCurrentStudent);
  // Cmd+Enter で送信
  document.getElementById('commIndBody')?.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') { e.preventDefault(); commIndividualSend(); }
  });
}

function loadIndividualTemplate(type) {
  const id = COMM_STATE.selectedStudentId;
  if (!id) return;
  if (type === 'dunning') {
    const m = buildMailFor(id);
    if (m) {
      document.getElementById('commIndSubject').value = m.subject;
      document.getElementById('commIndBody').value = m.body;
    }
  } else if (type === 'stripe_invite') {
    const m = buildStripeInviteFor(id);
    if (m) {
      document.getElementById('commIndSubject').value = m.subject;
      document.getElementById('commIndBody').value = m.body;
    }
  }
}

function commIndividualSend() {
  const id = COMM_STATE.selectedStudentId;
  if (!id) return;
  const s = STATE.data.students.find(x => x.id === id);
  if (!s) return;
  const email = getEmail(id);
  if (!email) { alert('メアドが未登録です'); return; }
  const subject = sanitizeSubject(document.getElementById('commIndSubject').value);
  const body = document.getElementById('commIndBody').value;
  if (!subject.trim() || !body.trim()) { alert('件名と本文を入力してください'); return; }
  if (!mailtoSafetyCheck(email, subject, body)) return;
  window.open(mailtoUrl(email, subject, body), '_blank');
  appendCommHistory({
    type: 'individual',
    studentId: id,
    studentName: s.name,
    email,
    subject,
    body,
  });
  alert(`✉ ${s.name} 様のメーラーを開きました`);
  // 履歴反映のため再描画
  renderCommIndividualEditor();
}

// ===== 送信履歴 =====

function renderCommHistory() {
  const list = document.getElementById('commHistoryList');
  if (!list) return;
  const history = getCommHistory().slice(0, 100);
  if (!history.length) {
    list.innerHTML = `<div style="color:var(--text-muted);text-align:center;padding:2rem">送信履歴がまだありません</div>`;
    return;
  }
  list.innerHTML = history.map(h => {
    const dt = new Date(h.sentAt).toLocaleString('ja-JP');
    if (h.type === 'broadcast') {
      const recipientNames = (h.recipients || []).slice(0, 5).map(r => escapeHtml(r.name)).join(', ');
      const more = (h.recipients || []).length > 5 ? ` 他${h.recipients.length - 5}名` : '';
      return `
        <div style="padding:0.7rem;margin-bottom:0.5rem;background:rgba(236,72,153,0.06);border-left:3px solid var(--accent);border-radius:6px">
          <div style="display:flex;justify-content:space-between;align-items:baseline;gap:0.5rem">
            <div style="font-weight:600">📢 ${escapeHtml(h.subject || '(件名なし)')}</div>
            <div style="font-size:0.75rem;color:var(--text-muted)">${dt}</div>
          </div>
          <div style="font-size:0.78rem;color:var(--text-muted);margin-top:0.3rem">${h.recipientCount}名に送信 (${h.method === 'bcc_copy' ? 'BCC一括コピー' : '順次メーラー'})</div>
          <div style="font-size:0.78rem;color:var(--text-muted);margin-top:0.2rem">${recipientNames}${more}</div>
        </div>
      `;
    }
    return `
      <div style="padding:0.7rem;margin-bottom:0.5rem;background:rgba(99,102,241,0.06);border-left:3px solid var(--primary);border-radius:6px">
        <div style="display:flex;justify-content:space-between;align-items:baseline;gap:0.5rem">
          <div style="font-weight:600">📨 ${escapeHtml(h.subject || '(件名なし)')}</div>
          <div style="font-size:0.75rem;color:var(--text-muted)">${dt}</div>
        </div>
        <div style="font-size:0.78rem;color:var(--text-muted);margin-top:0.3rem">→ ${escapeHtml(h.studentName || '(不明)')} (${escapeHtml(h.email || '')})</div>
      </div>
    `;
  }).join('');
}

function commHistoryClear() {
  if (!confirm('送信履歴を全削除します。この操作は取り消せません。続行しますか？')) return;
  STATE.overrides.commHistory = [];
  saveOverrides();
  renderCommHistory();
  alert('🗑 送信履歴を全削除しました');
}

// === v2 チャット (CEO 側) ===

const CHAT_API = '/payment/api/chat';
const CHAT_PW_KEY = 'juku-payment-chat-pw-v1';

const CHAT_STATE = {
  threads: [],
  currentThread: null,        // selected thread_id
  currentStudent: null,       // selected student name
  lastTs: 0,
  pollTimer: null,
  threadsTimer: null,
  pw: '',
  setupRequired: false,
};

function chatHeaders() {
  return CHAT_STATE.pw ? { 'X-Admin-Password': CHAT_STATE.pw } : {};
}

async function chatApi(method, params = {}, body = null) {
  const url = method === 'GET'
    ? `${CHAT_API}?${new URLSearchParams(params).toString()}`
    : CHAT_API;
  const opts = {
    method,
    headers: { 'Accept': 'application/json', ...chatHeaders() },
  };
  if (body) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  }
  const r = await fetch(url, opts);
  let data = null;
  try { data = await r.json(); } catch (e) {}
  if (!r.ok) {
    if (r.status === 503) CHAT_STATE.setupRequired = true;
    const msg = (data && (data.message || data.error)) || `HTTP ${r.status}`;
    const err = new Error(msg);
    err.status = r.status;
    err.data = data;
    throw err;
  }
  CHAT_STATE.setupRequired = false;
  return data;
}

function renderChat() {
  // パスワード保存値を反映
  CHAT_STATE.pw = localStorage.getItem(CHAT_PW_KEY) || '';
  const pwEl = document.getElementById('chatAdminPw');
  if (pwEl && !pwEl.value) pwEl.value = CHAT_STATE.pw;
  // パスワードあれば即読込
  if (CHAT_STATE.pw) {
    fetchThreads().catch(() => {});
    if (!CHAT_STATE.threadsTimer) {
      CHAT_STATE.threadsTimer = setInterval(() => {
        if (document.querySelector('.tab-active')?.dataset.tab === 'chat') {
          fetchThreads().catch(() => {});
        }
      }, 7000);
    }
  } else {
    document.getElementById('chatThreadList').innerHTML = `
      <div style="padding:2rem;text-align:center;color:var(--text-muted);font-size:0.85rem">
        管理パスワードを入力 → 🔄 で読込
      </div>
    `;
  }
}

async function fetchThreads() {
  try {
    const data = await chatApi('GET', { action: 'threads' });
    CHAT_STATE.threads = data.threads || [];
    document.getElementById('chatSetupHint').style.display = 'none';
    renderThreadList();
    updateGlobalUnread();
  } catch (e) {
    if (e.status === 503) {
      document.getElementById('chatSetupHint').style.display = 'block';
      document.getElementById('chatThreadList').innerHTML = `
        <div style="padding:1.5rem;text-align:center;color:var(--warning);font-size:0.85rem">
          🔧 セットアップ未完了
        </div>
      `;
    } else if (e.status === 401) {
      document.getElementById('chatThreadList').innerHTML = `
        <div style="padding:1.5rem;text-align:center;color:var(--error);font-size:0.85rem">
          🔒 認証失敗 (パスワード違い)
        </div>
      `;
    } else {
      document.getElementById('chatThreadList').innerHTML = `
        <div style="padding:1.5rem;text-align:center;color:var(--error);font-size:0.85rem">
          ⚠ ${escapeHtml(e.message)}
        </div>
      `;
    }
  }
}

function updateGlobalUnread() {
  const total = CHAT_STATE.threads.reduce((sum, t) => sum + (t.unread_admin || 0), 0);
  const badge = document.getElementById('chatGlobalUnread');
  if (!badge) return;
  if (total > 0) {
    badge.textContent = total > 99 ? '99+' : String(total);
    badge.classList.remove('hidden');
  } else {
    badge.classList.add('hidden');
  }
}

function renderThreadList() {
  const q = document.getElementById('chatThreadSearch')?.value?.trim().toLowerCase() || '';
  const list = document.getElementById('chatThreadList');
  if (!list) return;
  let threads = CHAT_STATE.threads.slice();
  if (q) {
    threads = threads.filter(t => (t.student_name || '').toLowerCase().includes(q) || t.thread_id.includes(q));
  }
  // 未読降順 + 最終時刻降順
  threads.sort((a, b) => {
    if ((b.unread_admin || 0) !== (a.unread_admin || 0)) return (b.unread_admin || 0) - (a.unread_admin || 0);
    return (b.last_msg_at || 0) - (a.last_msg_at || 0);
  });
  document.getElementById('chatThreadCountTag').textContent = `${CHAT_STATE.threads.length} スレッド`;
  if (!threads.length) {
    list.innerHTML = `<div style="padding:2rem;text-align:center;color:var(--text-muted);font-size:0.85rem">スレッドがまだありません<br><br>個別送信タブで「💬 チャット招待」ボタンから招待 URL を発行してください。</div>`;
    return;
  }
  list.innerHTML = threads.map(t => {
    const sid = t.thread_id;
    const isActive = CHAT_STATE.currentThread === sid;
    const dt = t.last_msg_at ? new Date(t.last_msg_at) : null;
    const time = dt ? `${String(dt.getHours()).padStart(2,'0')}:${String(dt.getMinutes()).padStart(2,'0')}` : '';
    const unread = t.unread_admin || 0;
    return `
      <div class="chat-thread-row${isActive ? ' active' : ''}" data-thread="${escapeHtml(sid)}" data-name="${escapeHtml(t.student_name || '')}">
        <div class="chat-thread-name">${escapeHtml(t.student_name || `#${sid}`)}</div>
        <div class="chat-thread-preview">${escapeHtml(t.last_msg_preview || '(メッセージなし)')}</div>
        <div class="chat-thread-meta">
          <span class="chat-thread-time">${time}</span>
          ${unread > 0 ? `<span class="chat-unread-badge">${unread}</span>` : ''}
        </div>
      </div>
    `;
  }).join('');
  list.onclick = (e) => {
    const row = e.target.closest('.chat-thread-row');
    if (!row) return;
    selectThread(row.dataset.thread, row.dataset.name);
  };
}

async function selectThread(threadId, studentName) {
  CHAT_STATE.currentThread = threadId;
  CHAT_STATE.currentStudent = studentName;
  CHAT_STATE.lastTs = 0;
  document.getElementById('chatHeader').innerHTML = `
    <div style="display:flex;align-items:center;gap:0.6rem">
      <div style="font-weight:700;font-size:1rem">${escapeHtml(studentName || `#${threadId}`)}</div>
      <span style="color:var(--text-muted);font-size:0.78rem">スレッド ID: ${escapeHtml(threadId)}</span>
    </div>
  `;
  document.getElementById('chatMessages').innerHTML = '<div style="padding:2rem;text-align:center;color:var(--text-muted)">読込中…</div>';
  document.getElementById('chatInputArea').style.display = 'flex';
  renderThreadList();  // active 強調
  await fetchChatMessages(true);
  await markThreadRead(threadId);
  startMessagePolling();
}

async function fetchChatMessages(initial) {
  if (!CHAT_STATE.currentThread) return;
  try {
    const data = await chatApi('GET', {
      action: 'messages',
      thread: CHAT_STATE.currentThread,
      since: String(CHAT_STATE.lastTs),
    });
    const msgs = data.messages || [];
    const container = document.getElementById('chatMessages');
    if (initial) container.innerHTML = '';
    if (msgs.length === 0 && initial) {
      container.innerHTML = `<div style="padding:2rem;text-align:center;color:var(--text-muted);font-size:0.9rem">まだメッセージはありません</div>`;
    } else if (msgs.length > 0) {
      // empty state クリア
      if (initial && container.querySelector('div[style*="text-align:center"]')) {
        container.innerHTML = '';
      }
      appendChatMessages(msgs);
      CHAT_STATE.lastTs = data.next_since || msgs[msgs.length - 1].ts;
    }
  } catch (e) {
    console.error('[chat] fetch failed', e);
  }
}

function appendChatMessages(msgs) {
  const container = document.getElementById('chatMessages');
  let lastDay = container.dataset.lastDay || '';
  msgs.forEach(m => {
    const d = new Date(m.ts);
    const day = `${d.getFullYear()}/${String(d.getMonth()+1).padStart(2,'0')}/${String(d.getDate()).padStart(2,'0')}`;
    if (day !== lastDay) {
      const div = document.createElement('div');
      div.className = 'chat-day-divider';
      div.textContent = day;
      container.appendChild(div);
      lastDay = day;
    }
    const time = `${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`;
    const isMe = m.sender === 'admin';
    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble ' + (isMe ? 'me' : 'peer');
    bubble.innerHTML = escapeHtml(m.body) + `<div class="chat-bubble-meta">${isMe ? '塾長' : (CHAT_STATE.currentStudent || '相手')} ${time}</div>`;
    container.appendChild(bubble);
  });
  container.dataset.lastDay = lastDay;
  setTimeout(() => container.scrollTop = container.scrollHeight, 30);
}

function startMessagePolling() {
  if (CHAT_STATE.pollTimer) clearInterval(CHAT_STATE.pollTimer);
  CHAT_STATE.pollTimer = setInterval(() => {
    if (document.hidden) return;
    if (document.querySelector('.tab-active')?.dataset.tab !== 'chat') return;
    if (!CHAT_STATE.currentThread) return;
    fetchChatMessages(false).catch(() => {});
    markThreadRead(CHAT_STATE.currentThread).catch(() => {});
  }, 5000);
}

async function markThreadRead(threadId) {
  try {
    await chatApi('POST', {}, { action: 'read', thread: threadId, reader: 'admin' });
    // ローカル状態更新
    const t = CHAT_STATE.threads.find(x => x.thread_id === threadId);
    if (t) t.unread_admin = 0;
    updateGlobalUnread();
    renderThreadList();
  } catch (e) {}
}

async function chatSendFromAdmin() {
  if (!CHAT_STATE.currentThread) return;
  const input = document.getElementById('chatInputBody');
  const body = input.value.trim();
  if (!body) return;
  const btn = document.getElementById('chatSendBtn');
  btn.disabled = true;
  try {
    const data = await chatApi('POST', {}, {
      action: 'send',
      thread: CHAT_STATE.currentThread,
      sender: 'admin',
      body,
      student_name: CHAT_STATE.currentStudent || '',
    });
    input.value = '';
    chatAutosize(input);
    appendChatMessages([data.message]);
    CHAT_STATE.lastTs = data.message.ts;
    fetchThreads().catch(() => {});  // スレッド一覧の last_msg_preview 更新
  } catch (e) {
    alert('送信失敗: ' + (e.message || ''));
  } finally {
    btn.disabled = input.value.trim().length === 0;
  }
}

function chatAutosize(ta) {
  ta.style.height = '42px';
  ta.style.height = Math.min(ta.scrollHeight, 140) + 'px';
}

async function generateChatInvite(studentId, studentName) {
  if (!CHAT_STATE.pw) {
    alert('チャットタブで管理パスワードを設定してください');
    return null;
  }
  try {
    const data = await chatApi('POST', {}, {
      action: 'invite',
      thread: String(studentId),
      student_name: studentName,
      expiry_days: 365,
    });
    const url = `${location.origin}/payment/chat.html?token=${encodeURIComponent(data.token)}`;
    return url;
  } catch (e) {
    alert('招待 URL 発行失敗: ' + (e.message || ''));
    return null;
  }
}

function copyChatInviteForCurrentStudent() {
  const id = COMM_STATE.selectedStudentId;
  if (!id) { alert('生徒を選択してください'); return; }
  const s = STATE.data.students.find(x => x.id === id);
  if (!s) return;
  generateChatInvite(s.id, s.name).then(url => {
    if (!url) return;
    copyToClipboard(url);
    // 本文に「{{chatLink}}」プレースホルダがあれば置換
    const bodyEl = document.getElementById('commIndBody');
    if (bodyEl && bodyEl.value.includes('{{chatLink}}')) {
      bodyEl.value = bodyEl.value.replaceAll('{{chatLink}}', url);
    } else if (bodyEl && bodyEl.value && !bodyEl.value.includes(url)) {
      // 末尾に追記の選択肢
      if (confirm(`✅ 招待 URL をクリップボードにコピーしました\n${url.slice(0, 60)}...\n\nメール本文の末尾にも追加しますか?`)) {
        bodyEl.value += `\n\n▼ チャット (アプリ内で塾長と直接やり取り)\n${url}\n※ このリンクはご家庭専用です。第三者に共有しないでください。`;
      }
    } else {
      alert(`✅ 招待 URL をクリップボードにコピーしました\n${url}\n\nメール本文に貼付けて保護者に送信してください。`);
    }
  });
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
  document.getElementById('setStripeCustomerPortal').value = SETTINGS.stripeCustomerPortalUrl || '';

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
  document.getElementById('setStripeInviteSubject').value = SETTINGS.stripeInviteSubject || DEFAULT_STRIPE_INVITE_SUBJECT;
  document.getElementById('setStripeInviteBody').value = SETTINGS.stripeInviteBody || DEFAULT_STRIPE_INVITE_BODY;
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
  SETTINGS.stripeInviteSubject = document.getElementById('setStripeInviteSubject').value;
  SETTINGS.stripeInviteBody = document.getElementById('setStripeInviteBody').value;
  SETTINGS.stripePaymentLink = document.getElementById('setStripeCommon').value.trim();
  SETTINGS.stripeCustomerPortalUrl = document.getElementById('setStripeCustomerPortal').value.trim();
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
    if (!confirm('メールテンプレート (督促 + Stripe案内) を初期値に戻しますか？')) return;
    document.getElementById('setMailSubject').value = DEFAULT_MAIL_SUBJECT;
    document.getElementById('setMailBody').value = DEFAULT_MAIL_BODY;
    document.getElementById('setStripeInviteSubject').value = DEFAULT_STRIPE_INVITE_SUBJECT;
    document.getElementById('setStripeInviteBody').value = DEFAULT_STRIPE_INVITE_BODY;
  });

  // 月初 Stripe 取込リマインダー
  const aib = document.getElementById('autoImportRunBtn');
  if (aib) aib.addEventListener('click', runAutoImport);
  const aid = document.getElementById('autoImportDismissBtn');
  if (aid) aid.addEventListener('click', dismissAutoImport);

  // 連絡センター (Communication)
  document.querySelectorAll('[data-comm-tab]').forEach(t => {
    t.addEventListener('click', () => switchCommSub(t.dataset.commTab));
  });
  ['commFilterStatus','commFilterGrade','commFilterCourse','commFilterUnpaid'].forEach(id => {
    document.getElementById(id)?.addEventListener('change', renderCommBroadcastPreview);
  });
  document.getElementById('commBroadcastPreviewBtn')?.addEventListener('click', commBroadcastPreview);
  document.getElementById('commBroadcastSendBtn')?.addEventListener('click', commBroadcastSendSequential);
  document.getElementById('commBroadcastBccBtn')?.addEventListener('click', commBroadcastBccCopy);
  document.getElementById('commBroadcastResendBtn')?.addEventListener('click', commBroadcastSendResend);
  document.getElementById('commBroadcastSaveTplBtn')?.addEventListener('click', commBroadcastSaveTemplate);
  document.getElementById('commBroadcastLoadTplBtn')?.addEventListener('click', commBroadcastLoadTemplate);
  document.getElementById('commIndividualSearch')?.addEventListener('input', () => {
    clearTimeout(window._commSearchTimer);
    window._commSearchTimer = setTimeout(renderCommIndividualList, 200);
  });
  document.getElementById('commHistoryClearBtn')?.addEventListener('click', commHistoryClear);

  // チャット (CEO 側)
  const pwEl = document.getElementById('chatAdminPw');
  if (pwEl) {
    pwEl.addEventListener('change', (e) => {
      CHAT_STATE.pw = e.target.value.trim();
      localStorage.setItem(CHAT_PW_KEY, CHAT_STATE.pw);
      fetchThreads().catch(() => {});
    });
  }
  document.getElementById('chatRefreshBtn')?.addEventListener('click', () => fetchThreads().catch(() => {}));
  document.getElementById('chatThreadSearch')?.addEventListener('input', () => {
    clearTimeout(window._chatSearchTimer);
    window._chatSearchTimer = setTimeout(renderThreadList, 200);
  });
  const chatInput = document.getElementById('chatInputBody');
  if (chatInput) {
    chatInput.addEventListener('input', (e) => {
      document.getElementById('chatSendBtn').disabled = e.target.value.trim().length === 0;
      chatAutosize(e.target);
    });
    chatInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
        e.preventDefault();
        chatSendFromAdmin();
      }
    });
  }
  document.getElementById('chatSendBtn')?.addEventListener('click', chatSendFromAdmin);
  // SIGNING_SECRET 生成ヘルパ (Vercel 設定用)
  document.getElementById('chatGenSecretBtn')?.addEventListener('click', () => {
    const arr = new Uint8Array(32);
    crypto.getRandomValues(arr);
    const secret = Array.from(arr).map(b => b.toString(16).padStart(2, '0')).join('');
    const out = document.getElementById('chatGeneratedSecret');
    out.textContent = secret;
    copyToClipboard(secret);
    setTimeout(() => alert(`✅ 生成 + クリップボードにコピーしました\n\nVercel Dashboard → Settings → Environment Variables で\n  Name: CHAT_SIGNING_SECRET\n  Value: (貼付け)\nを追加してください。`), 100);
  });

  // Email 一括登録
  const eib = document.getElementById('emailImportBtn');
  if (eib) eib.addEventListener('click', openEmailImportModal);
  const eip = document.getElementById('emailImportPreviewBtn');
  if (eip) eip.addEventListener('click', renderEmailImportPreview);
  const eia = document.getElementById('emailImportApplyBtn');
  if (eia) eia.addEventListener('click', applyEmailImport);
  const eit = document.getElementById('emailImportInput');
  if (eit) eit.addEventListener('input', () => {
    // 自動プレビュー (デバウンス)
    clearTimeout(window._emailPreviewTimer);
    window._emailPreviewTimer = setTimeout(renderEmailImportPreview, 400);
  });

  // 2026-05-07 追加: 生徒追加モーダル
  const asb = document.getElementById('addStudentBtn');
  if (asb) asb.addEventListener('click', openAddStudentModal);
  const ascb = document.getElementById('addStudentCancelBtn');
  if (ascb) ascb.addEventListener('click', closeAddStudentModalSafe);
  const assb = document.getElementById('addStudentSaveBtn');
  if (assb) assb.addEventListener('click', saveNewStudent);

  // Stripe Invite (一斉送信)
  const sib = document.getElementById('stripeInviteBtn');
  if (sib) sib.addEventListener('click', openStripeInviteModal);
  const sip = document.getElementById('stripeInvitePreviewBtn');
  if (sip) sip.addEventListener('click', previewStripeInvite);
  const siu = document.getElementById('stripeInviteUnsentBtn');
  if (siu) siu.addEventListener('click', () => bulkStripeInviteSequential({ onlyUnsent: true }));
  const sia = document.getElementById('stripeInviteAllBtn');
  if (sia) sia.addEventListener('click', () => bulkStripeInviteSequential({ onlyUnsent: false }));

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
  const pdBtn = document.getElementById('bulkPastDueBtn');
  if (pdBtn) pdBtn.addEventListener('click', sendBulkPastDueInvoices);
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
  document.getElementById('invoiceDownloadBtn').addEventListener('click', async (e) => {
    const id = parseInt(e.target.dataset.studentId, 10);
    if (id) {
      const btn = e.target;
      btn.disabled = true; const orig = btn.textContent; btn.textContent = '⏳ 生成中…';
      try { await generateInvoicePDF(id, true); }
      finally { btn.disabled = false; btn.textContent = orig; }
    }
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
  // 2026-05-07: クラウド sync 初期化 (token があれば pull → local 上書き)
  updateSyncStatusBar();
  await CloudSync.bootstrap();
  populateAllFilters();
  refresh();

  document.getElementById('monthInput').addEventListener('change', (e) => {
    STATE.currentMonth = e.target.value;
    const tag = document.getElementById('stripeMonthTag');
    if (tag) tag.textContent = STATE.currentMonth;
    const itag = document.getElementById('importMonthTag');
    if (itag) itag.textContent = `対象月: ${STATE.currentMonth}`;
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
  const stripeMonthTag = document.getElementById('stripeMonthTag');
  if (stripeMonthTag) stripeMonthTag.textContent = STATE.currentMonth;
  const stripeBtn = document.getElementById('stripeImportBtn');
  if (stripeBtn) stripeBtn.addEventListener('click', importFromStripe);
}

init().then(() => {
  if (window._needsImport) showInitialImportBanner();
  maybeShowAutoImportBanner();
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
