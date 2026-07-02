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
  if (!STATE.overrides.regLinks) STATE.overrides.regLinks = {};         // 2026-06-01: Stripe登録↔名簿 紐付け
  if (!STATE.overrides.studentEdits) STATE.overrides.studentEdits = {}; // 2026-06-03: 既存生徒の編集 上書き
  if (!Array.isArray(STATE.overrides.importedAppIds)) STATE.overrides.importedAppIds = []; // 2026-06-30: 入塾申込フォーム 取込済み course_application id
  // newStudents を STATE.data.students に in-memory merge (id 重複は新生徒側を採用)
  mergeNewStudentsIntoData();
  // 編集 (コース/月謝/学年/氏名) を上書き適用
  applyStudentEdits();
}

// 2026-06-03: newStudents の元オブジェクトを STATE.data.students と参照共有しないための安全コピー。
// applyStudentEdits は STATE.data.students を破壊的に書き換えるため、コピーを入れておかないと
// overrides.newStudents (= 追加時の素の値) まで汚染され、「編集を取消」で元に戻せなくなる (C-1)。
function cloneStudentForData(s) {
  return { ...s, courses: Array.isArray(s.courses) ? s.courses.slice() : s.courses };
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
      STATE.data.students.push(cloneStudentForData(ns));  // 参照共有を切る (C-1)
      existingIds.add(ns.id);
    }
  }
  // nextStudentId も追従 (= 次の追加で重複しないよう)
  const maxId = Math.max(STATE.data.nextStudentId || 1, ...newStudents.map(s => (s.id || 0) + 1));
  STATE.data.nextStudentId = maxId;
}

// 2026-06-03 追加: 既存生徒の編集 (コース/月謝/学年/氏名) を STATE.data.students に上書き適用。
// data.json (元データ) は不変のまま、studentEdits[id] にある変更フィールドだけを in-memory で重ねる。
// load / cloud pull のたびに再適用 (= 元データ再取得で編集が消えないよう冪等に重ねる)。
function applyStudentEdits() {
  if (!STATE.data || !STATE.data.students) return;
  const edits = STATE.overrides.studentEdits || {};
  for (const s of STATE.data.students) {
    const e = edits[s.id];
    if (!e || typeof e !== 'object') continue;
    if (typeof e.name === 'string' && e.name.trim()) s.name = e.name;
    if (typeof e.grade === 'string') s.grade = e.grade;
    if (Array.isArray(e.courses)) s.courses = e.courses.slice();  // slice で studentEdits との参照共有を切る
    if (typeof e.fee === 'number' && isFinite(e.fee) && e.fee >= 0) s.fee = e.fee;
  }
  normalizeStudentCourses();   // コースID→正式名 正規化 (map ロード後の全 sync 経路で適用)
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
  // Reviewer A HIGH #4: 同名生徒の重複チェック (異体字/かな差も吸収して正規化・2026-06-02)
  const normName = normalizeName(name);
  const dup = normName ? STATE.data.students.find(s => normalizeName(s.name) === normName) : null;
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

  // in-memory にも追加 (即時反映)。参照共有を切る (C-1: 後で編集しても newStudents 原本を汚さない)
  STATE.data.students.push(cloneStudentForData(newStudent));
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

// =============================================================
// 2026-06-30: 入塾申込フォーム取り込み
//   Web 入塾申込フォーム → POST /api/course-applications → course_applications(pending) を
//   この月謝名簿 (newStudents) に塾長操作で取り込む。
//   公開フォームは admin token を持てず、overrides blob は last-write-wins で塾長ブラウザが丸ごと
//   上書きするため「サーバが横から blob を書く」自動同期は塾長の保存で消える恐れがある。→ 取り込みは
//   塾長ブラウザの STATE 内で行い、通常の saveOverrides/CloudSync 経路で保存する (単一 writer を維持)。
//   取込済み id は overrides.importedAppIds に記録し、一覧から除外する。
// =============================================================
const ENROLL_REFERRER = '入塾申込フォーム';

function openImportAppsModalSafe() {
  const m = document.getElementById('importAppsModal');
  if (!m) return;
  m.classList.remove('hidden');
  m.style.display = '';
}
function closeImportAppsModalSafe() {
  const m = document.getElementById('importAppsModal');
  if (!m) return;
  m.classList.add('hidden');
  m.style.display = 'none';
}

// 申込 note (■受講コース / ■金額 / ■保護者 …) から コース配列・月謝・振込人名カナ を抽出
function parseEnrollmentApp(app) {
  const note = (app && app.note) || '';
  let courses = [];
  const mCourse = note.match(/■受講コース[:：]\s*(.+)/);
  if (mCourse) {
    const raw = mCourse[1].trim();
    if (raw && raw !== 'なし') {
      // 区切りは 、(全角読点) のみ。ASCII ',' は金額 "25,000円" 内に出るため分割対象にしない。
      courses = raw.split(/[、，]/).map(s => s.replace(/\s*[（(][^）)]*[）)]\s*$/, '').trim()).filter(Boolean);
    }
  }
  // 月謝 = 受講料 (設備費を含まない = この名簿の月謝慣習に一致)
  let fee = 0;
  const mFee = note.match(/受講料\s*([\d,]+)\s*円/);
  if (mFee) fee = parseInt(mFee[1].replace(/,/g, ''), 10) || 0;
  // 振込人名(カナ): 保護者行の (カナ) を拾う (best-effort)
  let payerName = '';
  const mPayer = note.match(/■保護者[:：][^（(]*[（(]([ぁ-んァ-ヶー\s]+)[）)]/);
  if (mPayer) payerName = mPayer[1].trim();
  return { courses, fee, payerName };
}

async function fetchPendingEnrollmentApps() {
  const token = (typeof CloudSync !== 'undefined') ? CloudSync.getToken() : '';
  if (!token) return { error: 'auth' };
  try {
    const res = await fetch(`${API_BASE}/api/admin/course-applications?status=pending&limit=200`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    if (res.status === 401) return { error: 'auth' };
    if (!res.ok) return { error: `HTTP ${res.status}` };
    const data = await res.json();
    const imported = new Set(STATE.overrides.importedAppIds || []);
    const apps = (data.applications || []).filter(a => a && a.referrer === ENROLL_REFERRER && !imported.has(a.id));
    return { apps };
  } catch (e) {
    return { error: e.message || 'fetch失敗' };
  }
}

function updateImportAppsBadge(n) {
  const b = document.getElementById('importAppsBadge');
  if (!b) return;
  if (n > 0) { b.textContent = n; b.style.display = ''; }
  else { b.style.display = 'none'; }
}

async function renderImportAppsList() {
  const box = document.getElementById('importAppsList');
  if (!box) return;
  box.innerHTML = '<p style="color:#9ca3af;font-size:0.9rem;">読み込み中…</p>';
  const result = await fetchPendingEnrollmentApps();
  if (result.error === 'auth') {
    box.innerHTML = '<p style="color:#fbbf24;font-size:0.9rem;line-height:1.6;">⚠ クラウド未ログインです。右上の 🔒 から管理者ログインしてから「↻ 再読み込み」を押してください。</p>';
    updateImportAppsBadge(0);
    return;
  }
  if (result.error) {
    box.innerHTML = `<p style="color:#f87171;font-size:0.9rem;">取得に失敗しました: ${escapeHtml(result.error)}</p>`;
    return;
  }
  const apps = result.apps || [];
  updateImportAppsBadge(apps.length);
  if (!apps.length) {
    box.innerHTML = '<p style="color:#9ca3af;font-size:0.9rem;">未取り込みの申込はありません。</p>';
    return;
  }
  box.innerHTML = apps.map(app => {
    const p = parseEnrollmentApp(app);
    const chips = p.courses.map(c => `<span style="display:inline-block;background:rgba(99,102,241,0.18);border:1px solid rgba(99,102,241,0.4);border-radius:6px;padding:1px 7px;margin:2px 3px 0 0;font-size:0.74rem;">${escapeHtml(c)}</span>`).join('');
    return `
    <div style="border:1px solid rgba(255,255,255,0.12);border-radius:10px;padding:12px 14px;background:rgba(0,0,0,0.18);">
      <div style="display:flex;justify-content:space-between;gap:10px;align-items:baseline;">
        <div style="font-weight:700;font-size:1rem;">${escapeHtml(app.name)} <span style="font-weight:400;font-size:0.8rem;color:#9ca3af;">${escapeHtml(app.grade || '')}</span></div>
        <div style="font-weight:700;color:#a5b4fc;white-space:nowrap;">月謝 ¥${(p.fee || 0).toLocaleString()}</div>
      </div>
      <div style="font-size:0.78rem;color:#cbd5e1;margin-top:4px;">✉ ${escapeHtml(app.email || '-')} ／ ☎ ${escapeHtml(app.phone || '-')}</div>
      <div style="margin-top:6px;">${chips || '<span style="color:#9ca3af;font-size:0.76rem;">コース未取得 (取込後に変更可)</span>'}</div>
      <details style="margin-top:8px;"><summary style="cursor:pointer;font-size:0.76rem;color:#9ca3af;">申込内容を見る</summary><pre style="white-space:pre-wrap;font-size:0.74rem;color:#cbd5e1;margin:6px 0 0;font-family:inherit;">${escapeHtml(app.note || '(なし)')}</pre></details>
      <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:10px;flex-wrap:wrap;">
        <button class="btn btn-ghost btn-sm" data-dismiss="${app.id}">🗑 無視</button>
        <button class="btn btn-ghost btn-sm" data-import="${app.id}">✓ 名簿に取り込む</button>
        <button class="btn btn-primary btn-sm" data-import-invite="${app.id}" title="名簿に取り込み、続けて Stripe カード決済の案内メールを送信します">✉ 取込＋Stripe案内</button>
      </div>
    </div>`;
  }).join('');
  box.querySelectorAll('[data-import]').forEach(b => b.addEventListener('click', () => {
    const app = apps.find(a => String(a.id) === b.getAttribute('data-import'));
    if (app) importApplicationAsStudent(app);
  }));
  box.querySelectorAll('[data-import-invite]').forEach(b => b.addEventListener('click', () => {
    const app = apps.find(a => String(a.id) === b.getAttribute('data-import-invite'));
    if (app) importApplicationAndInvite(app);
  }));
  box.querySelectorAll('[data-dismiss]').forEach(b => b.addEventListener('click', () => {
    const id = parseInt(b.getAttribute('data-dismiss'), 10);
    if (confirm('この申込を一覧から消します (名簿には追加しません)。よろしいですか？')) dismissApplication(id);
  }));
}

function allocateNewStudentId() {
  const usedIds = new Set((STATE.data && STATE.data.students ? STATE.data.students : []).map(s => s.id));
  const newMax = (STATE.overrides.newStudents || []).reduce((mx, s) => Math.max(mx, s.id || 0), 0);
  let id = Math.max((STATE.data && STATE.data.nextStudentId) || 1, newMax + 1);
  while (usedIds.has(id)) id += 1;
  return id;
}

// 取り込みの中核 (alert/一覧再描画はしない)。成功時 {id, fee, cloudOk} / 中断時 null を返す。
async function _importApplicationCore(app) {
  const p = parseEnrollmentApp(app);
  const normName = (typeof normalizeName === 'function') ? normalizeName(app.name) : (app.name || '').trim();
  const dup = normName ? STATE.data.students.find(s => (typeof normalizeName === 'function' ? normalizeName(s.name) : s.name) === normName) : null;
  if (dup) {
    if (!confirm(`既に同名の生徒「${dup.name}」(ID #${dup.id}) がいます。\n本当に新規で取り込みますか？ (同姓同名なら OK)`)) return null;
  }
  const id = allocateNewStudentId();
  const newStudent = {
    id,
    name: app.name || '(無名)',
    grade: app.grade || '',
    email: app.email || '',
    courses: p.courses,
    enrollDate: STATE.currentMonth || todayMonth(),
    status: '通塾',
    fee: p.fee || 0,
    notes: (app.note || '') + `\n[入塾申込フォーム取込 app#${app.id}]`,
    addedVia: 'enrollment-application-import',
    addedAt: new Date().toISOString(),
  };
  if (!STATE.overrides.newStudents) STATE.overrides.newStudents = [];
  STATE.overrides.newStudents.push(newStudent);
  if (p.payerName) {
    if (!STATE.overrides.payerNames) STATE.overrides.payerNames = {};
    STATE.overrides.payerNames[id] = p.payerName;
  }
  if (app.email) {
    if (!STATE.overrides.emails) STATE.overrides.emails = {};
    STATE.overrides.emails[id] = app.email;
  }
  if (!Array.isArray(STATE.overrides.importedAppIds)) STATE.overrides.importedAppIds = [];
  if (!STATE.overrides.importedAppIds.includes(app.id)) STATE.overrides.importedAppIds.push(app.id);
  saveOverrides();

  STATE.data.students.push(cloneStudentForData(newStudent));
  STATE.data.nextStudentId = id + 1;
  populateAllFilters();
  refresh();

  let cloudOk = true;
  if (typeof CloudSync !== 'undefined' && CloudSync.bootstrapped && CloudSync.getToken()) {
    cloudOk = await CloudSync.pushNow();
  }
  return { id, fee: p.fee || 0, cloudOk, name: newStudent.name, grade: app.grade || '未設定' };
}

function _cloudMsg(cloudOk) {
  if (typeof CloudSync === 'undefined' || !CloudSync.getToken()) return 'ℹ クラウド未ログイン: localStorage のみ保存';
  return cloudOk ? '✓ クラウド同期完了 (携帯/PC 共有)' : '⚠ クラウド同期失敗 (右上 ⚠ から再試行)';
}

async function importApplicationAsStudent(app) {
  const r = await _importApplicationCore(app);
  if (!r) return;
  alert(`✓ ${r.name} さん (ID #${r.id}) を名簿に取り込みました。\n月謝 ¥${r.fee.toLocaleString()} / 学年 ${r.grade}\n\n${_cloudMsg(r.cloudOk)}`);
  renderImportAppsList();
}

// 取り込み + Stripe案内メール送信 (確認してから任意送信)。
async function importApplicationAndInvite(app) {
  const r = await _importApplicationCore(app);
  if (!r) return;
  const s = STATE.data.students.find(x => x.id === r.id);
  const mailMsg = await sendStripeInviteForStudent(s);
  alert(`✓ ${r.name} さん (ID #${r.id}) を名簿に取り込みました。\n月謝 ¥${r.fee.toLocaleString()} / 学年 ${r.grade}\n\n${mailMsg}\n${_cloudMsg(r.cloudOk)}`);
  renderImportAppsList();
}

// 1名に Stripe案内メールを送る。検証→確認→Resend(失敗時mailto)→送信済み記録。結果文字列を返す。
async function sendStripeInviteForStudent(s) {
  if (!s) return '⚠ 案内メール未送信: 生徒が見つかりません';
  const to = getEmail(s.id);
  if (!to) return '⚠ 案内メール未送信: メールアドレスが未登録です';
  const link = paymentLinkFor(s);
  if (!link || link === '(未設定)') {
    return `⚠ 案内メール未送信: 月謝 ¥${(s.fee || 0).toLocaleString()} の Stripe 決済リンクが未設定です\n(設定モーダルの「月謝額→決済リンク」に登録すると送れます)`;
  }
  const m = buildStripeInviteFor(s.id);
  if (!m || !m.to) return '⚠ 案内メール未送信: メール生成に失敗しました';
  const preview = (m.body || '').slice(0, 300) + ((m.body || '').length > 300 ? '…' : '');
  if (!confirm(`Stripe カード決済の案内メールを送信します。\n\n宛先: ${m.to}\n件名: ${m.subject}\n\n${preview}\n\n送信しますか？`)) {
    return 'ℹ 案内メールは送信しませんでした (取り込みのみ完了)';
  }
  // Resend API 直送 (サーバ側・モバイル可)。admin パスワードがあれば優先。
  const pw = (typeof CHAT_STATE !== 'undefined' && CHAT_STATE.pw) || ((typeof CHAT_PW_KEY !== 'undefined') ? localStorage.getItem(CHAT_PW_KEY) : '') || '';
  if (pw) {
    try {
      const res = await commIndividualSendResend(s, m.subject, m.body);
      if (res) {
        setStripeInviteSent(s.id, new Date().toISOString().slice(0, 10));
        saveOverrides();
        if (typeof CloudSync !== 'undefined' && CloudSync.bootstrapped && CloudSync.getToken()) await CloudSync.pushNow();
        return `✅ Stripe案内メールを送信しました (${m.to})`;
      }
    } catch (e) { /* fall through to mailto */ }
  }
  // フォールバック: メーラーで開く (Resend 未設定/失敗時)
  if (mailtoSafetyCheck(m.to, m.subject, m.body)) {
    window.open(mailtoUrl(m.to, m.subject, m.body), '_blank');
    setStripeInviteSent(s.id, new Date().toISOString().slice(0, 10));
    saveOverrides();
    if (typeof CloudSync !== 'undefined' && CloudSync.bootstrapped && CloudSync.getToken()) await CloudSync.pushNow();
    return `📧 メーラーを開きました (${m.to})。表示されたメールの送信ボタンを押してください\n(Resend直送には チャットタブで管理パスワード設定が必要です)`;
  }
  return '⚠ 本文が長くメーラーで開けませんでした。名簿の「➜送信」から手動送信してください';
}

async function dismissApplication(appId) {
  if (!Array.isArray(STATE.overrides.importedAppIds)) STATE.overrides.importedAppIds = [];
  if (!STATE.overrides.importedAppIds.includes(appId)) STATE.overrides.importedAppIds.push(appId);
  saveOverrides();
  if (typeof CloudSync !== 'undefined' && CloudSync.bootstrapped && CloudSync.getToken()) {
    await CloudSync.pushNow();
  }
  renderImportAppsList();
}

function openImportAppsModal() {
  openImportAppsModalSafe();
  renderImportAppsList();
}

// 起動時/ログイン後にバッジ件数だけ静かに更新
async function refreshImportAppsBadge() {
  if (typeof CloudSync === 'undefined' || !CloudSync.getToken()) return;
  const result = await fetchPendingEnrollmentApps();
  if (result && result.apps) updateImportAppsBadge(result.apps.length);
}

// ESC / overlay クリックで閉じる (申込取り込みモーダル)
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    const m = document.getElementById('importAppsModal');
    if (m && !m.classList.contains('hidden')) closeImportAppsModalSafe();
  }
});
document.addEventListener('click', (e) => {
  const m = document.getElementById('importAppsModal');
  if (m && !m.classList.contains('hidden') && e.target === m) closeImportAppsModalSafe();
});

// =============================================================
// 2026-06-03: 生徒編集モーダル (コース変更などを名簿から直接行う)
// =============================================================
function openEditStudentModalSafe() {
  const m = document.getElementById('editStudentModal');
  if (!m) return;
  m.classList.remove('hidden');
  m.style.display = '';        // inline 削除で CSS 定義 (display: grid) を復活
}
function closeEditStudentModalSafe() {
  const m = document.getElementById('editStudentModal');
  if (!m) return;
  m.classList.add('hidden');
  m.style.display = 'none';    // class が効かなくても確実に消す
}

// コース単価リスト (name → price) を courses.json から取得 (キャッシュ)
let COURSE_PRICE_LIST = null;
async function loadCoursePriceList() {
  if (COURSE_PRICE_LIST) return COURSE_PRICE_LIST;
  const list = [];
  try {
    const res = await fetch('courses.json?t=' + Date.now());
    if (res.ok) {
      const json = await res.json();
      for (const c of (json.courses || [])) if (c && c.name) list.push({ name: c.name, price: Number(c.price) || 0 });
      for (const o of (json.options || [])) if (o && o.name) list.push({ name: o.name, price: Number(o.price) || 0 });
    }
  } catch (e) { console.warn('[coursePriceList] load failed:', e); }
  COURSE_PRICE_LIST = list;
  return COURSE_PRICE_LIST;
}

// textarea のコース文字列 → 配列 (改行区切り・1行=1コース・重複除去)。
// カンマでは分割しない: カタログに「設備費 (¥1,500)」等カンマを含む名称があり、
// カンマ分割すると「設備費 (¥1」「500)」に破損してコース絞り込み等に波及するため (HIGH 修正)。
function parseCoursesText(text) {
  const arr = (text || '').split(/\n/).map(s => s.trim()).filter(Boolean);
  return [...new Set(arr)];
}

async function openEditStudentModal(id) {
  const s = STATE.data.students.find(st => st.id === id);
  if (!s) { alert('生徒が見つかりません (ID #' + id + ')'); return; }
  document.getElementById('editStudentId').value = String(id);
  document.getElementById('editStudentSubtitle').textContent = `ID #${id}（現在の氏名: ${s.name || '—'}）`;
  document.getElementById('editStudentName').value = s.name || '';
  // 学年 select: 既存値が option に無ければ動的追加してから選択
  const gradeSel = document.getElementById('editStudentGrade');
  const grade = s.grade || '';
  if (grade && ![...gradeSel.options].some(o => o.value === grade || o.textContent === grade)) {
    const opt = document.createElement('option'); opt.value = grade; opt.textContent = grade; gradeSel.appendChild(opt);
  }
  gradeSel.value = grade;
  document.getElementById('editStudentFee').value = (typeof s.fee === 'number') ? s.fee : '';
  document.getElementById('editStudentCourses').value = (s.courses || []).join('\n');  // 1行=1コース
  // 差額自動反映の基準 = 現在の月謝に既に織り込まれているコース集合 (= 現在のコース)
  editFeeBaseCourses = parseCoursesText(document.getElementById('editStudentCourses').value);
  document.getElementById('editStudentRecalcNote').textContent = '';
  // 「編集を取消」ボタンは studentEdits 済みの生徒だけ表示
  const hasEdit = !!(STATE.overrides.studentEdits && STATE.overrides.studentEdits[id]);
  const resetBtn = document.getElementById('editStudentResetBtn');
  if (resetBtn) resetBtn.style.display = hasEdit ? '' : 'none';
  await renderEditCourseChips();
  openEditStudentModalSafe();
  setTimeout(() => document.getElementById('editStudentName').focus(), 50);
}

// コース単価カタログ + 名簿に存在する全コースをチップ表示 (クリックでトグル)
async function renderEditCourseChips() {
  const wrap = document.getElementById('editStudentCourseChips');
  if (!wrap) return;
  const list = await loadCoursePriceList();
  const seen = new Set();
  const chips = [];
  for (const c of list) { if (!seen.has(c.name)) { seen.add(c.name); chips.push({ name: c.name, price: c.price }); } }
  // 名簿に存在する非カタログコースも候補に追加 (price 不明)
  for (const st of STATE.data.students) for (const cn of (st.courses || [])) {
    if (cn && !seen.has(cn)) { seen.add(cn); chips.push({ name: cn, price: null }); }
  }
  wrap.innerHTML = chips.map(c =>
    `<button type="button" class="course-chip" data-course="${escapeHtml(c.name)}">${escapeHtml(c.name)}${c.price ? `<span style="opacity:.55;margin-left:5px;">¥${c.price.toLocaleString()}</span>` : ''}</button>`
  ).join('');
  wrap.onclick = async (e) => {
    const b = e.target.closest('.course-chip'); if (!b) return;
    const name = b.dataset.course;
    const ta = document.getElementById('editStudentCourses');
    const cur = parseCoursesText(ta.value);
    if (cur.includes(name)) ta.value = cur.filter(x => x !== name).join('\n');  // トグル off
    else { cur.push(name); ta.value = cur.join('\n'); }                          // トグル on (1行=1コース)
    syncEditChipActive();
    await autoAdjustFeeForCourseChange();   // チップ変更分を月謝に差額自動反映
  };
  // textarea: 入力中はチップ表示を同期 (oninput)、入力確定 (blur=onchange) で月謝に差額反映
  const ta = document.getElementById('editStudentCourses');
  if (ta) {
    ta.oninput = syncEditChipActive;
    ta.onchange = autoAdjustFeeForCourseChange;
  }
  syncEditChipActive();
}

// textarea の内容に合わせてチップの active 表示を同期
function syncEditChipActive() {
  const ta = document.getElementById('editStudentCourses');
  if (!ta) return;
  const cur = new Set(parseCoursesText(ta.value));
  document.querySelectorAll('#editStudentCourseChips .course-chip').forEach(b => {
    b.classList.toggle('chip-active', cur.has(b.dataset.course));
  });
}

// コース → 月謝 「合計で上書き」(courses.json の単価合計でゼロから計算し直す)。
// 通常のコース変更は autoAdjustFeeForCourseChange の差額自動反映で済むが、
// 月謝を一度カタログ合計にリセットしたい時のためのボタン。
async function recalcEditFeeFromCourses() {
  const list = await loadCoursePriceList();
  const priceMap = {}; for (const c of list) priceMap[c.name] = c.price;
  const courses = parseCoursesText(document.getElementById('editStudentCourses').value);
  let sum = 0; const missing = [];
  for (const cn of courses) {
    if (priceMap[cn] != null) sum += priceMap[cn];
    else missing.push(cn);
  }
  // 上書きは設備費・割引・個別指導などの上乗せ分を消すため、現在額と差があれば確認
  const curFee = parseInt(document.getElementById('editStudentFee').value, 10);
  if (!isNaN(curFee) && curFee !== sum) {
    if (!confirm(`月謝をコース単価の合計 ¥${sum.toLocaleString()} で上書きします。\n現在の ¥${curFee.toLocaleString()} は消えます（設備費・割引・個別指導などの上乗せ分も消えます）。\n\nよろしいですか?`)) return;
  }
  document.getElementById('editStudentFee').value = sum;
  flashEditFee();
  editFeeBaseCourses = courses;   // 上書き後の基準を更新 (以後の差額反映の起点)
  if (!courses.length) setEditNote('コースが未入力です', true);
  else if (missing.length) setEditNote(`合計 ¥${sum.toLocaleString()} で上書き（カタログ未登録: ${missing.join('・')} は ¥0 換算 → 手動調整してください）`, true);
  else setEditNote(`合計 ¥${sum.toLocaleString()} で上書き（設備費・割引があれば手動調整）`, false);
}

// コース変更分を月謝に「差額」で自動反映する。設備費・個別指導などの上乗せ分を保つため
// 「合計で上書き」ではなく、追加/削除されたコースのカタログ単価だけを増減する。
// editFeeBaseCourses = 現在の月謝額に既に織り込まれているコース集合 (= 二重カウント防止の基準)。
let editFeeBaseCourses = [];
function setEditNote(msg, warn) {
  const note = document.getElementById('editStudentRecalcNote');
  if (!note) return;
  note.textContent = msg;
  note.style.color = warn ? '#fbbf24' : '#a5b4fc';   // 警告は橙・通常は藍
}
function flashEditFee() {
  const el = document.getElementById('editStudentFee');
  if (!el) return;
  el.classList.remove('fee-flash');
  void el.offsetWidth;          // reflow で再アニメーションをトリガー
  el.classList.add('fee-flash');
}
async function autoAdjustFeeForCourseChange() {
  const list = await loadCoursePriceList();
  const priceMap = {}; for (const c of list) priceMap[c.name] = c.price;
  const newCourses = parseCoursesText(document.getElementById('editStudentCourses').value);
  const baseSet = new Set(editFeeBaseCourses);
  const newSet = new Set(newCourses);
  const added = newCourses.filter(c => !baseSet.has(c));
  const removed = editFeeBaseCourses.filter(c => !newSet.has(c));
  if (!added.length && !removed.length) return;   // コース変化なし
  let delta = 0; const unknown = [];
  for (const c of added)   { if (priceMap[c] != null) delta += priceMap[c]; else unknown.push(c); }
  for (const c of removed) { if (priceMap[c] != null) delta -= priceMap[c]; else unknown.push(c); }
  editFeeBaseCourses = newCourses;   // 基準を更新 (二重カウント防止)
  if (delta !== 0) {
    const feeEl = document.getElementById('editStudentFee');
    const cur = parseInt(feeEl.value, 10);
    const raw = (isNaN(cur) ? 0 : cur) + delta;
    const next = Math.max(0, raw);
    feeEl.value = next;
    flashEditFee();
    if (raw < 0) {
      // 割引等で差額がマイナス → 黙って ¥0 にせず警告 (請求 0 円事故の防止)
      setEditNote('⚠ 月謝欄を ¥0 にしました（差額で計算するとマイナスになります）。割引・設備費を含む実額を手動でご入力ください。', true);
    } else {
      const parts = [];
      for (const c of added)   if (priceMap[c] != null) parts.push(`${c} +¥${priceMap[c].toLocaleString()}`);
      for (const c of removed) if (priceMap[c] != null) parts.push(`${c} −¥${priceMap[c].toLocaleString()}`);
      if (unknown.length) setEditNote(`月謝欄を ¥${next.toLocaleString()} に更新（${parts.join(' / ')}）。ただし ${unknown.join('・')} は単価カタログに無いため未調整 → 手動でご確認を`, true);
      else setEditNote(`月謝欄を ¥${next.toLocaleString()} に更新（${parts.join(' / ')}）`, false);
    }
  } else if (unknown.length) {
    setEditNote(`⚠ ${unknown.join('・')} は単価カタログに無いため月謝は自動調整していません。手動でご入力ください。`, true);
  }
}

async function saveStudentEdit() {
  const id = parseInt(document.getElementById('editStudentId').value, 10);
  const s = STATE.data.students.find(st => st.id === id);
  if (!s) { alert('生徒が見つかりません'); return; }
  // textarea を blur せず保存した場合の取りこぼし対策 (差額が未反映なら反映)。基準追従なので冪等。
  await autoAdjustFeeForCourseChange();
  const name = document.getElementById('editStudentName').value.trim();
  const grade = document.getElementById('editStudentGrade').value.trim();
  // 月謝: 全角数字→半角・カンマ/空白除去で「165,000」「１６５００」の取りこぼし/silent切り捨てを防ぐ
  const feeRaw = document.getElementById('editStudentFee').value
    .replace(/[０-９]/g, c => String.fromCharCode(c.charCodeAt(0) - 0xFEE0))
    .replace(/[,，\s]/g, '')
    .trim();
  const courses = parseCoursesText(document.getElementById('editStudentCourses').value);
  if (!name) { alert('氏名は必須です'); return; }
  const fee = parseInt(feeRaw, 10);
  if (isNaN(fee) || fee < 0) { alert('月謝は 0 以上の整数を入力してください'); return; }
  if (fee > 1000000) {
    if (!confirm(`月謝 ¥${fee.toLocaleString()} は通常より大きい値です。よろしいですか?`)) return;
  }
  // 月謝 ¥0 の保存は明示確認 (差額反映で気付かず ¥0 になった場合の請求漏れ防止)
  if (fee === 0) {
    if (!confirm('月謝が ¥0 です。本当に 0 円でよろしいですか?\n（この生徒は請求対象から外れます。割引・設備費を含む実額がある場合は入力し直してください）')) return;
  }
  // 月謝の桁ミス防止 (請求書 invoice は編集後 fee をそのまま請求額に使うため): 既存額と大きく乖離する場合は確認
  const oldFee = (typeof s.fee === 'number') ? s.fee : null;
  if (oldFee && oldFee > 0 && fee !== oldFee && fee <= 1000000) {
    const ratio = fee / oldFee;
    if (ratio >= 3 || ratio <= 1 / 3 || Math.abs(fee - oldFee) >= 50000) {
      if (!confirm(`月謝を ¥${oldFee.toLocaleString()} → ¥${fee.toLocaleString()} に変更します。\n変更幅が大きいため確認します（桁ミスや反映漏れにご注意ください）。\nコースを足した結果であればそのままで問題ありません。\n\n※ 未払い者へ「請求書(invoice)」を発行すると、この金額がそのまま請求額になります。\n\nこの金額でよろしいですか?`)) return;
    }
  }
  // 氏名変更は Stripe 照合/振込人名マッチに影響するため軽く確認
  if (name !== (s.name || '')) {
    if (!confirm(`氏名を「${s.name}」→「${name}」に変更します。\n(銀行明細・カード照合は振込人名/カナで行うため通常は影響しませんが念のため確認)\n\n続行しますか?`)) return;
  }

  if (!STATE.overrides.studentEdits) STATE.overrides.studentEdits = {};
  STATE.overrides.studentEdits[id] = { name, grade, courses, fee, editedAt: new Date().toISOString() };
  // 取消後の再編集を尊重: tombstone から外す (= 再び remote merge 対象に戻す・regLinks と同方式)
  if (typeof CloudSync !== 'undefined' && CloudSync._deletedStudentEditSids) CloudSync._deletedStudentEditSids.delete(String(id));
  applyStudentEdits();   // in-memory 即反映
  saveOverrides();       // localStorage + CloudSync push (debounced)
  closeEditStudentModalSafe();
  populateAllFilters();
  refresh();

  // 即時 push (debounce 待たずに) — タブ閉じ・通信不安定で消失防止
  let cloudMsg = '';
  if (typeof CloudSync !== 'undefined' && CloudSync.bootstrapped && CloudSync.getToken()) {
    const ok = await CloudSync.pushNow();
    cloudMsg = ok ? '✓ クラウド同期完了 (携帯/PC 共有)' : '⚠ クラウド同期失敗 (右上 ⚠ アイコンクリックで再試行)';
  } else {
    cloudMsg = 'ℹ クラウド未ログイン: localStorage のみに保存 (右上 🔒 でログインすると同期)';
  }

  // 💴 月末引き落とし額の同期 (2026-06-06): 月末引き落としは登録(registration KV)の monthly_fee を使うため、
  // 名簿の月謝編集を「紐付け✓確定済み」の生徒だけ registration にも反映する。
  // → 月末引き落とし(preview/execute/この人だけ/滞納)が新金額になる。
  // 安全: 紐付け確定済みのみ(氏名推測マッチはしない=重複登録の誤更新防止)・PW未入力/未紐付けは silent fail させず明示。
  let feeSyncMsg = '';
  const _link = getRegLink(id);
  if (_link && _link.regId) {
    const _pw = getChatPw();
    if (!_pw) {
      feeSyncMsg = '\n\n⚠ 月末引き落とし額は未更新です: チャット管理パスワード未入力。\n(「💬 チャット」等のタブで管理パスワードを入力後、もう一度保存すると引き落とし額も同期されます)';
    } else {
      try {
        const _r = await fetch('/payment/api/admin-update-registration', {
          method: 'POST',
          headers: { 'X-Admin-Password': _pw, 'Content-Type': 'application/json' },
          body: JSON.stringify({
            action: 'update_fee',
            registrationId: _link.regId,
            monthly_fee: fee,
            fee_breakdown: courses.join(' / '),
            expectCustomerId: _link.customerId || undefined,
          }),
        });
        const _d = await _r.json().catch(() => ({}));
        if (_r.ok && _d.ok) {
          feeSyncMsg = `\n\n✓ 月末引き落とし額も ¥${(_d.prev || 0).toLocaleString()} → ¥${fee.toLocaleString()} に同期しました (次回引き落としから反映)`;
          try { if (typeof loadRegisteredCustomers === 'function') await loadRegisteredCustomers(true); } catch (e) {}
        } else if (_r.status === 401) {
          feeSyncMsg = '\n\n⚠ 月末引き落とし額は未更新: 管理パスワードが違います';
        } else if (_r.status === 404) {
          feeSyncMsg = '\n\nℹ 月末引き落とし額の同期はスキップ: この生徒の登録が見つかりません(未紐付け/解除済み)';
        } else if (_r.status === 409) {
          feeSyncMsg = `\n\n⚠ 月末引き落とし額は未更新: ${_d.message || '紐付けと登録の顧客IDが不一致(重複登録の可能性)'}`;
        } else {
          feeSyncMsg = `\n\n⚠ 月末引き落とし額の同期に失敗: ${_d.message || ('HTTP ' + _r.status)}`;
        }
      } catch (e) {
        feeSyncMsg = `\n\n⚠ 月末引き落とし額の同期エラー: ${e && e.message ? e.message : e}`;
      }
    }
  }

  alert(`✓ ${name} さん (ID #${id}) の情報を更新しました。\n\n学年: ${grade || '未設定'} / 月謝: ¥${fee.toLocaleString()}\nコース: ${courses.join('・') || '(なし)'}\n\n${cloudMsg}${feeSyncMsg}`);
}

// 編集を取消して元データ (data.json) の値に戻す
async function resetStudentEdit() {
  const id = parseInt(document.getElementById('editStudentId').value, 10);
  if (!STATE.overrides.studentEdits || !STATE.overrides.studentEdits[id]) { closeEditStudentModalSafe(); return; }
  if (!confirm('この生徒の編集を取り消して、元データ (data.json) の値に戻しますか?\n(元データを再反映するためページを再読込します)')) return;
  delete STATE.overrides.studentEdits[id];
  // 取消した sid を記録 → 直後の pushNow pre-pull merge で remote から復活させない (regLinks と同方式・CRITICAL C-2)
  if (typeof CloudSync !== 'undefined') {
    if (!CloudSync._deletedStudentEditSids) CloudSync._deletedStudentEditSids = new Set();
    CloudSync._deletedStudentEditSids.add(String(id));
  }
  saveOverrides();
  closeEditStudentModalSafe();
  if (typeof CloudSync !== 'undefined' && CloudSync.bootstrapped && CloudSync.getToken()) {
    const ok = await CloudSync.pushNow();
    if (!ok) {
      // push 失敗のまま reload すると、pull で別端末の古い edit が復活しうる → reload を止める
      alert('⚠ クラウド同期に失敗しました。取消をクラウドに反映できていません。\n通信を確認し、右上の ⚠ アイコンから再同期してください。\n(このまま再読込すると別端末の古い編集が復活する可能性があります)');
      return;
    }
  }
  alert('↺ 編集を取り消しました。元データを反映するため再読込します。');
  location.reload();
}

// ESC / overlay クリックで編集モーダルを閉じる
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    const m = document.getElementById('editStudentModal');
    if (m && !m.classList.contains('hidden')) closeEditStudentModalSafe();
  }
});
document.addEventListener('click', (e) => {
  const m = document.getElementById('editStudentModal');
  if (m && !m.classList.contains('hidden') && e.target === m) closeEditStudentModalSafe();
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
  'regLinks',      // 2026-06-01: Stripe登録(reg_id/cus_id)↔生徒名簿(studentId) の確定紐付け
  'studentEdits',  // 2026-06-03: 既存生徒の編集 (コース/月謝/学年/氏名) 上書き
]);
// 2026-06-03 (H-1) 後方互換のため寛容化: shape (object か) だけ厳格に見て、未知の top-level key は
// 「拒否」ではなく「無視」する。旧来は未知 key が1つでもあると false を返し、呼び出し側が
// 「remote を捨てて自分の local を push で上書き」してしまうため、新クライアントが追加した
// 新 key (regLinks→studentEdits 等) を旧クライアントが pull するたびに remote 全体を巻き戻す
// データ消失ベクトルがあった。未知 key は読み飛ばす設計に変更し、将来の key 追加でも壊れないようにする。
function _isValidOverrides(obj) {
  if (!obj || typeof obj !== 'object' || Array.isArray(obj)) return false;
  const unknown = Object.keys(obj).filter(k => !OVERRIDE_VALID_KEYS.has(k));
  if (unknown.length) {
    // 拒否はしない (= 後方互換)。新しいバージョンが追加した key の可能性が高い。
    console.warn('[overrides] 未知の top-level key を無視します (新バージョン由来の可能性):', unknown);
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
            if (_isValidOverrides(remoteOv)) {
              if (Array.isArray(remoteOv.newStudents)) {
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
              // 2026-06-01: regLinks も「remote にあって local に無い studentId」を merge (同時紐付けの消失防止)
              if (remoteOv.regLinks && typeof remoteOv.regLinks === 'object' && !Array.isArray(remoteOv.regLinks)) {
                if (!STATE.overrides.regLinks) STATE.overrides.regLinks = {};
                const delSet = this._deletedRegLinkSids || null;
                let regMerged = 0;
                for (const sid of Object.keys(remoteOv.regLinks)) {
                  // local に無く、かつ「このセッションで解除した sid」でなければ取り込む (解除の即復活を防ぐ)
                  if (!(sid in STATE.overrides.regLinks) && !(delSet && delSet.has(sid))) {
                    STATE.overrides.regLinks[sid] = remoteOv.regLinks[sid];
                    regMerged++;
                  }
                }
                if (regMerged) {
                  localStorage.setItem(LS_KEY, JSON.stringify(STATE.overrides));
                  console.log('[CloudSync] pushNow: merged', regMerged, 'remote regLinks before push');
                }
              }
              // 2026-06-03: studentEdits も「remote にあって local に無い studentId」を merge (別デバイスでの編集消失防止)
              if (remoteOv.studentEdits && typeof remoteOv.studentEdits === 'object' && !Array.isArray(remoteOv.studentEdits)) {
                if (!STATE.overrides.studentEdits) STATE.overrides.studentEdits = {};
                const editDelSet = this._deletedStudentEditSids || null;  // 取消した sid は remote から復活させない
                let editMerged = 0;
                for (const sid of Object.keys(remoteOv.studentEdits)) {
                  if (!(sid in STATE.overrides.studentEdits) && !(editDelSet && editDelSet.has(sid))) {
                    STATE.overrides.studentEdits[sid] = remoteOv.studentEdits[sid];
                    editMerged++;
                  }
                }
                if (editMerged) {
                  localStorage.setItem(LS_KEY, JSON.stringify(STATE.overrides));
                  if (typeof applyStudentEdits === 'function') applyStudentEdits();
                  if (typeof populateAllFilters === 'function') populateAllFilters();
                  if (typeof refresh === 'function') refresh();
                  console.log('[CloudSync] pushNow: merged', editMerged, 'remote studentEdits before push');
                }
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
          if (!STATE.overrides.regLinks) STATE.overrides.regLinks = {};
          if (!STATE.overrides.studentEdits) STATE.overrides.studentEdits = {};
          localStorage.setItem(LS_KEY, JSON.stringify(STATE.overrides));
          // remote 側の newStudents を STATE.data.students に in-memory merge (= 別デバイスで追加した生徒を取り込む)
          mergeNewStudentsIntoData();
          // remote 側の編集 (コース/月謝等) も上書き適用
          applyStudentEdits();
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
        if (!STATE.overrides.studentEdits) STATE.overrides.studentEdits = {};
        localStorage.setItem(LS_KEY, JSON.stringify(STATE.overrides));
        // 別デバイスで追加した生徒を in-memory merge
        if (typeof mergeNewStudentsIntoData === 'function') mergeNewStudentsIntoData();
        // 別デバイスでの編集 (コース/月謝等) を上書き適用
        if (typeof applyStudentEdits === 'function') applyStudentEdits();
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

// === regLinks: Stripe登録(reg_id/cus_id) ↔ 生徒名簿(studentId) の確定紐付け (2026-06-01) ===
function getRegLink(studentId) {
  return (STATE.overrides.regLinks && STATE.overrides.regLinks[studentId]) || null;
}
function setRegLink(studentId, regId, customerId, by = 'manual') {
  if (!STATE.overrides.regLinks) STATE.overrides.regLinks = {};
  STATE.overrides.regLinks[studentId] = {
    regId: regId || '',
    customerId: customerId || '',
    linkedAt: new Date().toISOString(),
    linkedBy: by,
  };
  // 再紐付けしたら「解除済み」記録から外す (再確定を尊重)
  if (typeof CloudSync !== 'undefined' && CloudSync._deletedRegLinkSids) CloudSync._deletedRegLinkSids.delete(String(studentId));
  saveOverrides();
}
function deleteRegLink(studentId) {
  if (STATE.overrides.regLinks && (studentId in STATE.overrides.regLinks)) {
    delete STATE.overrides.regLinks[studentId];
    // 解除した sid を記録 → 直後の pushNow pre-pull merge で remote から復活させない (CloudSync ON 時も自端末の解除を確実化)
    if (typeof CloudSync !== 'undefined') {
      if (!CloudSync._deletedRegLinkSids) CloudSync._deletedRegLinkSids = new Set();
      CloudSync._deletedRegLinkSids.add(String(studentId));
    }
    saveOverrides();
  }
}
// regId → studentId の逆引き Map (Step2 の入金自動反映で使用)
// 二端末競合等で同一カードが複数生徒に紐付いた場合は、最新 (linkedAt) の紐付けを採用し警告を出す
// (挿入順の非決定的な後勝ちを避け、入金反映先を一意・決定的にする・2026-06-02 強化)。
function buildRegIdToStudentMap() {
  const m = {};
  const at = {};  // rid → 採用中の linkedAt
  const links = STATE.overrides.regLinks || {};
  for (const sid of Object.keys(links)) {
    const link = links[sid];
    const rid = link && link.regId;
    if (!rid) continue;
    const t = link.linkedAt || '';
    if (rid in m) {
      console.warn('[regLink] 同一カードが複数生徒に紐付いています:', rid, '→ #' + m[rid], '/ #' + parseInt(sid, 10), '(最新の紐付けを採用)');
      if (t >= (at[rid] || '')) { m[rid] = parseInt(sid, 10); at[rid] = t; }
    } else {
      m[rid] = parseInt(sid, 10);
      at[rid] = t;
    }
  }
  return m;
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

// チャット管理パスワードの読込 (CHAT_STATE 優先 → localStorage)。registered-customers の取得と
// 「カード列が出ない理由」ヒントが pw 有無を同一ソースで判定するため共通化 (2026-06-01)。
function getChatPw() {
  return (typeof CHAT_STATE !== 'undefined' && CHAT_STATE.pw) || localStorage.getItem('juku-payment-chat-pw-v1') || '';
}

async function loadRegisteredCustomers(force = false) {
  const now = Date.now();
  if (!force && STRIPE_CUST_CACHE.loadedAt && now - STRIPE_CUST_CACHE.loadedAt < 60000) return STRIPE_CUST_CACHE.customers;
  if (STRIPE_CUST_CACHE.loading) return STRIPE_CUST_CACHE.customers;
  const pw = getChatPw();
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

// 'YYYY-MM' → 'YYYY年M月分' (請求書 description 用・形式外は '〜分' のまま)
function monthLabelJa(month) {
  const m = /^(\d{4})-(\d{2})$/.exec(month || '');
  return m ? `${m[1]}年${Number(m[2])}月分` : `${month}分`;
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

// 生徒の Stripe 登録状態を解決 (2026-06-01)
//   linked    = regLinks で確定済み (reg が現存 or cache 未ロード)
//   candidate = 未確定だが matchCustomerForStudent がヒット (塾長が「✓確定」で linked 化)
//   none      = 該当 Stripe 登録なし
function resolveRegForStudent(student) {
  if (!student) return { reg: null, status: 'none', link: null };
  const link = getRegLink(student.id);
  if (link && link.regId) {
    if (STRIPE_CUST_CACHE.customers.length) {
      const reg = STRIPE_CUST_CACHE.customers.find(c => c.registrationId === link.regId);
      if (reg) return { reg, status: 'linked', link };
      // cache はあるが reg が消えている (キャンセル/退塾処理済) → 確定無効化して候補に落とす
    } else {
      // cache 未ロード時は確定情報だけで linked 扱い
      return { reg: { registrationId: link.regId, customerId: link.customerId, studentName: student.name }, status: 'linked', link };
    }
  }
  const cand = matchCustomerForStudent(student);
  if (cand) return { reg: cand, status: 'candidate', link: null };
  return { reg: null, status: 'none', link: null };
}

// 紐付け状態バッジ (確定=緑 / 候補=黄+確定ボタン / 無=灰)。data 属性は renderAll の onclick が拾う。
function stripeRegBadge(student) {
  const r = resolveRegForStudent(student);
  if (r.status === 'linked') {
    const cid = (r.reg && r.reg.customerId) || (r.link && r.link.customerId) || '';
    const regName = (r.reg && r.reg.studentName) || '';
    const titleTxt = regName ? `Stripe登録: ${regName} (${cid})` : cid;
    return `<span class="badge" style="background:rgba(16,185,129,0.18);color:#34d399;padding:2px 8px;border-radius:6px;font-size:0.78rem;font-weight:600;" title="${escapeHtml(titleTxt)}">✓ 紐付け済</span>`
      + ` <button class="icon-btn" data-action="unlink-reg" title="この紐付けを解除">解除</button>`;
  }
  if (r.status === 'candidate') {
    const nm = escapeHtml(r.reg.studentName || '');
    return `<span class="badge" style="background:rgba(245,158,11,0.18);color:#fbbf24;padding:2px 8px;border-radius:6px;font-size:0.78rem;font-weight:600;" title="候補: ${nm}">候補</span>`
      + ` <button class="icon-btn" data-action="link-reg" data-reg-id="${escapeHtml(r.reg.registrationId || '')}" data-customer-id="${escapeHtml(r.reg.customerId || '')}" title="${nm} の登録と紐付けを確定">✓確定</button>`;
  }
  return `<span class="badge" style="background:rgba(107,114,128,0.18);color:#9ca3af;padding:2px 8px;border-radius:6px;font-size:0.78rem;">未登録</span>`;
}

// 生徒一覧 行の「🎓講習費用」ボタン。確定カード紐付け(getRegLink.regId)がある生徒のみ有効化。
// 候補(fuzzy)や未登録は無効化+理由ツールチップ (誤って別人/カード無しに課金しないため)。
function spotChargeBtnForStudent(student) {
  const link = getRegLink(student.id);
  const cardReady = !!(link && link.regId);
  if (cardReady) {
    return `<button class="icon-btn" data-action="spot-charge" title="講習費用などを任意金額で今すぐ1回だけ請求 (月謝は変わりません)" style="color:#a78bfa;border-color:rgba(139,92,246,0.45);">🎓講習費用</button>`;
  }
  return `<button class="icon-btn" disabled title="カード未登録のため講習費用のカード請求はできません。先に「✓確定」でカード紐付けが必要です。" style="opacity:0.35;cursor:not-allowed;">🎓講習費用</button>`;
}

// 候補バッジの「✓確定」ボタン → 手動で紐付け確定 (renderAll 等で共通利用)
function handleLinkRegClick(studentId, regId, customerId) {
  if (!regId) { alert('登録情報が見つかりません。画面を再読込してください。'); return; }
  const student = STATE.data.students.find(x => x.id === studentId);
  const nm = student ? student.name : `#${studentId}`;
  // Stripe 側の登録名を提示し、fuzzy マッチの誤紐付け(別人の登録)を塾長が確認できるようにする
  const regCust = STRIPE_CUST_CACHE.customers.find(c => c.registrationId === regId);
  const regName = regCust ? regCust.studentName : '';
  const regLine = regName ? `Stripe登録名「${regName}」(${customerId || regId})` : `Stripe登録 (${customerId || regId})`;
  if (!confirm(`名簿「${nm}」さん を ${regLine} と紐付けますか?\n\n⚠ 名前が一致しているか確認してください。別人の登録を誤って紐付けると、その生徒の入金が誤って反映されます。\n\n以降この生徒は月末引き落とし結果が自動で入金反映の対象になります。\n紐付けは「解除」ボタンでいつでも取り消せます。`)) return;
  setRegLink(studentId, regId, customerId, 'manual');
  refresh();
}

// 紐付け済みバッジの「解除」ボタン → 確定紐付けを取り消す (誤紐付けの復旧用)
function handleUnlinkRegClick(studentId) {
  const student = STATE.data.students.find(x => x.id === studentId);
  const nm = student ? student.name : `#${studentId}`;
  if (!getRegLink(studentId)) { refresh(); return; }
  if (!confirm(`${nm} さんの Stripe 登録との紐付けを解除しますか?\n\n入金の自動反映の対象から外れます。再度「✓確定」で紐付け直せます。`)) return;
  deleteRegLink(studentId);
  refresh();
}

// === Step3: カード登録あり・名簿未登録 の取り込み (2026-06-01) ===
// コースID → コース名 マップ (courses.json から構築。register登録のID を名簿のコース名に変換)
let COURSE_NAME_MAP = null;
async function loadCourseMap() {
  if (COURSE_NAME_MAP) return COURSE_NAME_MAP;
  const map = {};
  try {
    const res = await fetch('courses.json?t=' + Date.now());
    if (res.ok) {
      const json = await res.json();
      for (const c of (json.courses || [])) if (c && c.id) map[c.id] = c.name;
      for (const o of (json.options || [])) if (o && o.id) map[o.id] = o.name;
    }
  } catch (e) { console.warn('[courseMap] load failed:', e); }
  COURSE_NAME_MAP = map;
  return COURSE_NAME_MAP;
}
function courseNameFromId(id) {
  return (COURSE_NAME_MAP && COURSE_NAME_MAP[id]) || id;
}

// 2026-06-03: カード登録サイト由来のコースID (long-1 / soukei / grammar-2 / kou2-grammar 等) を
// courses.json の正式名 (英語長文レベル１ / 早慶クラス 等) に正規化し、名前版と同一視する。
// data.json (元データ) は不変・STATE.data 上の in-memory のみ書き換え。編集して保存すれば恒久反映。
// COURSE_NAME_MAP 未ロード時は no-op (init で loadCourseMap を await してから呼ぶ)。
// 2026-06-03: 表記ゆれ統合 — 末尾の「生」「コース」を外す + NFKC(全角半角)吸収で正式名に
// 完全一致した時だけ寄せる。曖昧/部分マッチはせず、必ず courses.json の正式名(正規形)を返すので
// 誤統合しない。例: 中学2年生→中学2年 / 国公立難関大学コース→国公立難関大学 / 英検準2級(半角)→英検準２級。
// 浪人生 等の正式名は先に catalog 判定で素通りするため削られない。
const COURSE_VARIANT_SUFFIXES = ['生', 'コース'];
// 塾長承認済みの明示エイリアス (2026-06-03): 完全一致のみ・曖昧マッチは増やさない。
const COURSE_ALIASES = {
  '中学1年': '中学基礎中学1年',
  '中学1年生': '中学基礎中学1年',
};
function nfkcKey(s) { try { return s.normalize('NFKC'); } catch (e) { return s; } }
// nfkcToName: NFKC キー → 正式名。catalog を後入れして alias より優先 (正式名を絶対に壊さない)。
function buildNfkcToName(catalogNames) {
  const m = new Map();
  for (const [k, v] of Object.entries(COURSE_ALIASES)) m.set(nfkcKey(k), v);
  for (const n of catalogNames) m.set(nfkcKey(n), n);   // catalog が最優先
  return m;
}
function canonicalCourseName(c, catalogNames, nfkcToName) {
  const mapped = courseNameFromId(c);            // id→正式名 (正式名/未知文字列はそのまま)
  if (catalogNames.has(mapped)) return mapped;   // 既に正式名 (id由来含む) はそのまま (最優先・誤変換防止)
  let hit = nfkcToName.get(nfkcKey(mapped));      // NFKC/エイリアスで正式名に一致 (全角半角ゆれ吸収)
  if (hit) return hit;
  for (const suf of COURSE_VARIANT_SUFFIXES) {   // 末尾「生」「コース」を外して再照合
    if (mapped.length > suf.length && mapped.endsWith(suf)) {
      hit = nfkcToName.get(nfkcKey(mapped.slice(0, -suf.length)));
      if (hit) return hit;
    }
  }
  return mapped;                                 // どれにも当たらなければ原文字列のまま
}
function normalizeStudentCourses() {
  if (!COURSE_NAME_MAP || !STATE.data || !STATE.data.students) return;
  const catalogNames = new Set(Object.values(COURSE_NAME_MAP));   // 照合先 = courses.json の正式名集合
  const nfkcToName = buildNfkcToName(catalogNames);
  for (const s of STATE.data.students) {
    if (!Array.isArray(s.courses) || !s.courses.length) continue;
    const mapped = s.courses.map(c => canonicalCourseName(c, catalogNames, nfkcToName));  // id正規化 + 表記ゆれ統合
    const deduped = [...new Set(mapped)];                                       // 重複を統合
    if (deduped.length !== s.courses.length || deduped.some((c, i) => c !== s.courses[i])) {
      s.courses = deduped;
    }
  }
}

// reg (Stripe登録) → 名簿の生徒を逆引き (matchCustomerForStudent の逆方向)
function findStudentForReg(reg) {
  if (!reg) return null;
  const rNorm = normalizeName(reg.studentName);
  if (!rNorm) return null;
  for (const s of STATE.data.students) {
    const sNorm = normalizeName(s.name);
    if (sNorm && (sNorm === rNorm || sNorm.includes(rNorm) || rNorm.includes(sNorm))) return s;
  }
  // 括弧内候補との一致
  const rCands = extractNameCandidates(reg.studentName).map(normalizeName).filter(Boolean);
  for (const s of STATE.data.students) {
    const sCands = extractNameCandidates(s.name).map(normalizeName).filter(Boolean);
    for (const rc of rCands) for (const sc of sCands) if (rc === sc) return s;
  }
  return null;
}

// 未紐付けの登録者を名簿に追加 + カード紐付け (saveNewStudent の採番/同名チェックを流用)
async function addStudentFromReg(reg) {
  const name = (reg.studentName || '').trim();
  if (!name) { alert('登録者名が空です。'); return; }
  const fee = parseInt(reg.amount || reg.monthly_fee || 0, 10) || 0;
  // register で選択したコースID → コース名に変換して名簿に反映
  await loadCourseMap();
  const courseNames = (Array.isArray(reg.courses) ? reg.courses : []).map(courseNameFromId);
  const optionNames = (Array.isArray(reg.options) ? reg.options : []).map(courseNameFromId);
  // 同名チェック (異体字/かな差も吸収して正規化) — 重複登録/同一人物の二重追加を防ぐ。
  // 既存生徒が見つかれば、新規追加せず「その生徒への紐付け」を第一候補として提示する。
  const nn = normalizeName(name);
  const dup = nn ? STATE.data.students.find(s => normalizeName(s.name) === nn) : null;
  if (dup) {
    const linkInstead = confirm(`既に名簿に「${dup.name}」(ID #${dup.id}) がいます。\n\n【OK】= この生徒のカードに紐付ける (重複を作りません・推奨)\n【キャンセル】= 別人として新規追加するか選び直す`);
    if (linkInstead) { await linkRegToStudent(reg, dup.id); return; }
    if (!confirm(`「${name}」さんを別人として新規追加します。よろしいですか?\n(同一人物の場合は中止してください)`)) return;
  }
  const courseLine = courseNames.length ? `\nコース: ${courseNames.join('・')}` : '';
  const optionLine = optionNames.length ? `\nオプション: ${optionNames.join('・')}` : '';
  if (!confirm(`「${name}」さん (${reg.grade || '学年未設定'}) を名簿に追加しますか?${courseLine}${optionLine}\n月謝 ¥${fee.toLocaleString()} / 保護者 ${reg.parentName || '—'}\n\nカード登録 (${reg.customerId || reg.registrationId}) と自動で紐付けます。`)) return;
  // id 採番 (saveNewStudent と同一ロジック・衝突回避)
  const usedIds = new Set(STATE.data.students.map(s => s.id));
  const newStudentsMax = (STATE.overrides.newStudents || []).reduce((mx, s) => Math.max(mx, s.id || 0), 0);
  let id = Math.max(STATE.data.nextStudentId || 1, newStudentsMax + 1);
  while (usedIds.has(id)) id += 1;
  const notesParts = ['カード登録から追加'];
  if (optionNames.length) notesParts.push('オプション: ' + optionNames.join('・'));
  const newStudent = {
    id, name,
    grade: reg.grade || '',
    email: reg.email || '',
    courses: courseNames,
    enrollDate: STATE.currentMonth || '',
    status: '通塾',
    fee,
    notes: notesParts.join(' / '),
    addedVia: 'reg-auto-add',
    addedAt: new Date().toISOString(),
  };
  if (!STATE.overrides.newStudents) STATE.overrides.newStudents = [];
  STATE.overrides.newStudents.push(newStudent);
  STATE.data.students.push(cloneStudentForData(newStudent));  // 参照共有を切る (C-1)
  STATE.data.nextStudentId = id + 1;
  // 追加と同時にカード紐付け (原子化・再追加防止) + 振込人名/メール学習
  setRegLink(id, reg.registrationId, reg.customerId, 'auto-add');
  if (reg.parentName) setPayerName(id, reg.parentName);
  if (reg.email) setEmail(id, reg.email);
  saveOverrides();
  populateAllFilters();
  refresh();
  // 即 push (タブ閉じ・通信不安定での消失防止) — saveNewStudent と同様に await で成否を反映
  let cloudMsg = '';
  if (typeof CloudSync !== 'undefined' && CloudSync.bootstrapped && CloudSync.getToken()) {
    const ok = await CloudSync.pushNow();
    cloudMsg = ok ? '\n\n✓ クラウド同期完了 (携帯/PC 共有)' : '\n\n⚠ クラウド同期に失敗しました (右上の同期アイコンから再試行できます)';
  } else {
    cloudMsg = '\n\nℹ クラウド未ログイン: この端末のみに保存されました';
  }
  alert(`✓ ${name} さん (ID #${id}) を名簿に追加し、カード登録と紐付けました。${cloudMsg}`);
}

// カード登録(reg) を「既存の名簿生徒」に紐付け (新規追加せず重複を防ぐ・2026-06-02)
// 名前の字体ゆれ(澤/沢・髙/高)やかな漢字差で自動マッチしない既存生徒に、塾長が手動で紐付ける共通処理。
// 既存の手動「✓確定」(handleLinkRegClick) と同じ信頼モデル。1カード=1生徒の不変条件を保ち、誤紐付けは「解除」で取消可。
async function linkRegToStudent(reg, studentId, by = 'manual-existing') {
  const student = STATE.data.students.find(s => s.id === studentId);
  if (!student) { alert('生徒が見つかりません。画面を再読込してください。'); return; }
  if (!reg || !reg.registrationId) { alert('カード登録情報が見つかりません。'); return; }
  // 1) この生徒に既に別カードが紐付いていれば付け替え確認
  const existing = getRegLink(studentId);
  if (existing && existing.regId && existing.regId !== reg.registrationId) {
    if (!confirm(`${student.name} さんには既に別のカード登録が紐付いています。\n今回の登録 (${reg.customerId || reg.registrationId}) に付け替えますか?`)) return;
  }
  // 2) このカードが既に別の生徒に紐付いていれば、1カード=1生徒を保つため元を「全件」解除
  const links = STATE.overrides.regLinks || {};
  const otherSids = Object.keys(links).filter(sid => links[sid] && links[sid].regId === reg.registrationId && parseInt(sid, 10) !== studentId);
  if (otherSids.length) {
    const names = otherSids.map(sid => { const os = STATE.data.students.find(x => x.id === parseInt(sid, 10)); return os ? os.name : '#' + sid; }).join('、');
    if (!confirm(`このカード登録は既に「${names}」さんに紐付いています。\n${student.name} さんに付け替えますか? (元の紐付けは解除されます)`)) return;
    otherSids.forEach(sid => deleteRegLink(parseInt(sid, 10)));
  }
  // 3) 確定 — payerName/メールとも既存の手入力値は上書きしない (誤上書き防止)
  setRegLink(studentId, reg.registrationId, reg.customerId, by);
  if (reg.parentName && !getPayerName(studentId)) setPayerName(studentId, reg.parentName);
  if (reg.email && !getEmail(studentId)) setEmail(studentId, reg.email);
  saveOverrides();
  if (typeof populateAllFilters === 'function') populateAllFilters();
  refresh();
  let cloudMsg = '';
  if (typeof CloudSync !== 'undefined' && CloudSync.bootstrapped && CloudSync.getToken()) {
    const ok = await CloudSync.pushNow();
    cloudMsg = ok ? '\n\n✓ クラウド同期完了 (携帯/PC 共有)' : '\n\n⚠ クラウド同期に失敗しました (右上の同期アイコンから再試行できます)';
  } else {
    cloudMsg = '\n\nℹ クラウド未ログイン: この端末のみに保存されました';
  }
  alert(`✓ ${student.name} さん (ID #${student.id}) にカード登録を紐付けました。\n以降この生徒は月末引き落とし結果が自動で入金反映の対象になります。${cloudMsg}`);
}

// 「カード登録あり・名簿未登録」パネルの「👤 既存に紐付け」→ 名簿生徒を検索して選ぶピッカー (2026-06-02)
// 自動照合が外れた既存生徒を、塾長が名前で探して紐付ける。新規追加(=重複)を回避するための導線。
function openLinkExistingPicker(reg) {
  if (!reg) return;
  const old = document.getElementById('linkExistingOverlay');
  if (old) old.remove();
  const regName = (reg.studentName || '').trim();
  const rNorm = normalizeName(regName);
  const rSurname = normalizeName(extractSurname(regName));
  // 候補スコア: 完全一致 > 部分一致 > 姓一致 > 通塾中 の順で上位に
  const rankOf = (s) => {
    const sn = normalizeName(s.name);
    if (!sn || !rNorm) return getStatus(s) === '通塾' ? 10 : 0;
    if (sn === rNorm) return 100;
    if (sn.includes(rNorm) || rNorm.includes(sn)) return 80;
    if (rSurname && rSurname.length >= 1 && sn.includes(rSurname)) return 50;
    return getStatus(s) === '通塾' ? 10 : 5;
  };
  const sorted = STATE.data.students.slice().sort((a, b) => rankOf(b) - rankOf(a) || a.id - b.id);

  const overlay = document.createElement('div');
  overlay.id = 'linkExistingOverlay';
  overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.62);z-index:10000;display:flex;align-items:flex-start;justify-content:center;padding:48px 16px;overflow:auto;';
  const box = document.createElement('div');
  box.style.cssText = 'background:#141426;border:1px solid rgba(255,255,255,0.12);border-radius:14px;max-width:560px;width:100%;box-shadow:0 18px 50px rgba(0,0,0,0.5);overflow:hidden;';
  box.innerHTML = `
    <div style="padding:16px 18px;border-bottom:1px solid rgba(255,255,255,0.08);">
      <div style="font-weight:700;color:#e5e7eb;font-size:1rem;">👤 既存の生徒に紐付け</div>
      <div style="color:#9ca3af;font-size:0.84rem;margin-top:4px;line-height:1.5;">
        カード登録 <strong style="color:#fbbf24;">「${escapeHtml(regName || '—')}」</strong>${reg.grade ? '（' + escapeHtml(reg.grade) + '）' : ''} を名簿の生徒に紐付けます。<br>
        新規追加せず<strong style="color:#34d399;">重複を防ぎます</strong>。名前の字体・ふりがな差があっても選べます。
      </div>
    </div>
    <div style="padding:12px 18px 0;">
      <input id="linkPickSearch" type="text" placeholder="氏名・学年・IDで検索" autocomplete="off"
        style="width:100%;box-sizing:border-box;padding:9px 12px;border-radius:8px;border:1px solid rgba(255,255,255,0.16);background:#0d0d1c;color:#e5e7eb;font-size:0.92rem;">
    </div>
    <div id="linkPickList" style="max-height:46vh;overflow:auto;padding:8px 12px 4px;"></div>
    <div style="padding:12px 18px;border-top:1px solid rgba(255,255,255,0.08);text-align:right;">
      <button data-link-cancel style="background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.16);color:#e5e7eb;padding:8px 16px;border-radius:8px;cursor:pointer;font-size:0.88rem;">キャンセル</button>
    </div>`;
  overlay.appendChild(box);
  document.body.appendChild(overlay);

  const listEl = box.querySelector('#linkPickList');
  const searchEl = box.querySelector('#linkPickSearch');
  const renderList = () => {
    const raw = searchEl.value.trim();
    const q = normalizeName(raw);
    let filtered = sorted.filter(s => {
      if (!raw) return true;
      if (String(s.id) === raw) return true;
      return normalizeName(s.name).includes(q) || normalizeName(s.grade || '').includes(q);
    });
    // ID完全一致は80件打ち切りで消えないよう最優先で先頭へ
    if (raw && /^\d+$/.test(raw)) {
      const i = filtered.findIndex(s => String(s.id) === raw);
      if (i > 0) filtered.unshift(filtered.splice(i, 1)[0]);
    }
    filtered = filtered.slice(0, 80);
    if (!filtered.length) {
      listEl.innerHTML = '<div style="color:#9ca3af;padding:14px;text-align:center;font-size:0.88rem;">該当する生徒がいません</div>';
      return 0;
    }
    listEl.innerHTML = filtered.map(s => {
      const r = rankOf(s);
      const linked = getRegLink(s.id);
      const otherLinked = linked && linked.regId && linked.regId !== reg.registrationId;
      const hi = r >= 80;
      const badge = hi ? ' <span style="color:#34d399;font-size:0.72rem;">候補</span>' : '';
      const warn = otherLinked ? ' <span style="color:#fbbf24;font-size:0.72rem;">別カード紐付け済</span>' : '';
      const st = getStatus(s);
      const stCol = st === '通塾' ? '#34d399' : (st === '退塾' ? '#f87171' : '#9ca3af');
      return `<button class="link-pick-row" data-sid="${s.id}" style="display:flex;align-items:center;justify-content:space-between;gap:10px;width:100%;text-align:left;background:${hi ? 'rgba(16,185,129,0.10)' : 'transparent'};border:1px solid ${hi ? 'rgba(16,185,129,0.35)' : 'rgba(255,255,255,0.07)'};border-radius:8px;padding:9px 12px;margin-bottom:6px;cursor:pointer;color:#e5e7eb;">
        <span style="font-weight:600;">${escapeHtml(s.name)}${badge}${warn}</span>
        <span style="color:#9ca3af;font-size:0.78rem;white-space:nowrap;">${escapeHtml(s.grade || '')} · <span style="color:${stCol};">${escapeHtml(st)}</span> · #${s.id}</span>
      </button>`;
    }).join('');
    return filtered.length;
  };
  // 姓で初期フィルタ → 0件なら全件に戻す
  searchEl.value = extractSurname(regName) || '';
  if (renderList() === 0 && searchEl.value) { searchEl.value = ''; renderList(); }
  setTimeout(() => { searchEl.focus(); searchEl.select(); }, 30);
  searchEl.addEventListener('input', renderList);

  const closeOverlay = () => { overlay.remove(); document.removeEventListener('keydown', onKey); };
  const onKey = (e) => { if (e.key === 'Escape') closeOverlay(); };
  document.addEventListener('keydown', onKey);
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay || e.target.closest('[data-link-cancel]')) { closeOverlay(); return; }
    const row = e.target.closest('.link-pick-row');
    if (!row) return;
    const sid = parseInt(row.dataset.sid, 10);
    closeOverlay();
    linkRegToStudent(reg, sid);
  });
}

// 全生徒タブ上部の「カード登録あり・名簿未登録」パネル
function renderUnlinkedRegsPanel() {
  const panel = document.getElementById('unlinkedRegsPanel');
  if (!panel) return;
  // 管理パスワード未入力の端末では registered-customers を取得できず、カード列が無言で
  // 全員「未登録」になる。原因 (pw 未入力) を明示し、チャットタブへ誘導する
  // (sendPastDueInvoiceFor / sendBulkPastDueInvoices の switchTab('chat') 誘導と同方針)。
  if (!getChatPw()) {
    panel.innerHTML = `
      <div style="background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.4);border-radius:10px;padding:12px 16px;margin-bottom:16px;">
        <div style="font-weight:700;color:#fbbf24;margin-bottom:4px;">🔒 管理パスワード未入力</div>
        <div style="color:#9ca3af;font-size:0.85rem;line-height:1.6;">
          この端末ではまだ管理パスワードを入力していないため、右端の<strong style="color:#e5e7eb;">「カード」列にカード登録状況が反映されていません</strong> (未登録と表示されます)。<br>
          チャットタブで管理パスワードを入力するとカード登録状況が表示されます。
        </div>
        <button class="btn btn-primary btn-sm" data-action="goto-chat-pw" style="margin-top:10px;">💬 チャットタブで管理パスワードを入力</button>
      </div>`;
    panel.onclick = (e) => {
      if (e.target.closest('[data-action="goto-chat-pw"]')) switchTab('chat');
    };
    return;
  }
  const regs = STRIPE_CUST_CACHE.customers || [];
  if (!regs.length) { panel.innerHTML = ''; return; }
  const linkedRegIds = new Set(Object.values(STATE.overrides.regLinks || {}).map(l => l && l.regId).filter(Boolean));
  const unlinked = regs.filter(r => {
    if (linkedRegIds.has(r.registrationId)) return false;  // 既に紐付け済み
    if (findStudentForReg(r)) return false;                // 名簿にいる → カード列で候補表示
    return true;                                           // 名簿に無い → 取り込み対象
  });
  if (!unlinked.length) { panel.innerHTML = ''; return; }
  panel._unlinked = unlinked;
  panel.innerHTML = `
    <div style="background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.4);border-radius:10px;padding:12px 16px;margin-bottom:16px;">
      <div style="font-weight:700;color:#fbbf24;margin-bottom:4px;">💳 カード登録あり・名簿と自動照合できず (${unlinked.length}件)</div>
      <div style="color:#9ca3af;font-size:0.8rem;margin-bottom:10px;">カード登録があるのに名簿と自動照合できなかった方です。<strong style="color:#e5e7eb;">既に名簿にいる場合は「👤 既存に紐付け」</strong>で重複を作らず紐付けてください。本当に名簿にいない新規の方だけ「＋名簿に追加」を使います。</div>
      <table class="table" style="width:100%;font-size:0.86rem;">
        <thead><tr style="color:#9ca3af;text-align:left;"><th>氏名</th><th>学年</th><th>保護者</th><th class="ta-r">月謝</th><th></th></tr></thead>
        <tbody>
        ${unlinked.map((r, i) => `<tr>
          <td class="name-cell">${escapeHtml(r.studentName || '')}</td>
          <td>${escapeHtml(r.grade || '—')}</td>
          <td>${escapeHtml(r.parentName || '—')}</td>
          <td class="ta-r fee-cell">${yen(r.amount || r.monthly_fee || 0)}</td>
          <td class="ta-r" style="white-space:nowrap;">
            <button class="btn btn-ghost btn-sm" data-action="link-existing-reg" data-reg-idx="${i}" title="既に名簿にいる生徒に紐付け (重複を作りません)">👤 既存に紐付け</button>
            <button class="btn btn-primary btn-sm" data-action="add-from-reg" data-reg-idx="${i}" title="名簿にいない新規の方として追加">＋名簿に追加</button>
          </td>
        </tr>`).join('')}
        </tbody>
      </table>
    </div>`;
  panel.onclick = (e) => {
    const linkBtn = e.target.closest('[data-action="link-existing-reg"]');
    if (linkBtn) {
      const reg = panel._unlinked && panel._unlinked[parseInt(linkBtn.dataset.regIdx, 10)];
      if (reg) openLinkExistingPicker(reg);
      return;
    }
    const addBtn = e.target.closest('[data-action="add-from-reg"]');
    if (addBtn) {
      const reg = panel._unlinked && panel._unlinked[parseInt(addBtn.dataset.regIdx, 10)];
      if (reg) addStudentFromReg(reg);
    }
  };
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
    if (!getChatPw()) {
      // pw 未入力では総数を取得できず 0 に見えるだけ。「登録者ゼロ」と誤認させない。
      text.innerHTML = `🔒 管理パスワード未入力のためカード登録状況を取得できません — <strong>チャットタブ</strong>で管理パスワードを入力してください`;
    } else {
      text.textContent = `💳 Stripe 登録者: 0 名 — まだカード登録した保護者がいません (登録 URL: /payment/register.html)`;
    }
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

  const pw = (typeof CHAT_STATE !== 'undefined' && CHAT_STATE.pw) || localStorage.getItem('juku-payment-chat-pw-v1') || '';
  if (!pw) { alert('管理パスワード未入力です。チャットタブで入力してください。'); switchTab('chat'); return; }

  // 二重送信防止: 同一行のボタンを一時 disabled
  const btn = document.querySelector(`tr[data-student-id="${studentId}"] [data-action="past-due-one"]`);
  if (btn) { if (btn.dataset.busy === '1') return; btn.dataset.busy = '1'; btn.disabled = true; const orig = btn.textContent; btn.textContent = '⏳'; }
  try {
    const res = await fetch('/payment/api/past-due-invoice', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Admin-Password': pw },
      body: JSON.stringify({ items: [{ customerId: cust.customerId, studentName: s.name, month, amount: fee, description: `通塾月謝 ${monthLabelJa(month)}` }] }),
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
      items.push({ customerId: cust.customerId, studentName: s.name, month, amount: s.fee, description: `通塾月謝 ${monthLabelJa(month)}` });
    }
  }
  if (!items.length) { alert(`Stripe 登録済の未払い者がいません (${month})`); return; }
  const total = items.reduce((sum, i) => sum + i.amount, 0);
  // 個別金額を含む詳細 confirm
  const itemList = items.slice(0, 10).map(i => `  • ${i.studentName} ¥${i.amount.toLocaleString()}`).join('\n');
  const more = items.length > 10 ? `\n  ...他 ${items.length - 10} 名` : '';
  if (!confirm(`【${month} 分 Stripe 請求書 一括発行】\n\n対象: ${items.length} 名\n合計: ¥${total.toLocaleString()}\n支払期限: 発行から 7 日後\n\n${itemList}${more}\n\n各保護者の Stripe 登録メアド宛に Stripe からメール送信されます。\n同じ生徒・同月の重複発行は自動で防がれます (90日間)。\n\n続行しますか?`)) return;

  const pw = (typeof CHAT_STATE !== 'undefined' && CHAT_STATE.pw) || localStorage.getItem('juku-payment-chat-pw-v1') || '';
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

  // Stripe 登録顧客を遅延ロード → 取得できたら「カード」列込みで再描画
  // 試行は1回だけ (無限ループ + 失敗時の毎描画再fetch を防止)。成功したらフラグを戻して再描画。
  if (!STRIPE_CUST_CACHE.customers.length && !STRIPE_CUST_CACHE.loadedAt && !STRIPE_CUST_CACHE._allTabTried) {
    STRIPE_CUST_CACHE._allTabTried = true;
    loadRegisteredCustomers().then((custs) => { if (custs && custs.length) { STRIPE_CUST_CACHE._allTabTried = false; renderAll(); } });
  }
  // Step3: カード登録あり・名簿未登録の取り込みパネル
  renderUnlinkedRegsPanel();

  if (!students.length) {
    tbody.innerHTML = `<tr><td colspan="10" class="empty">該当する生徒はいません</td></tr>`;
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
      <td class="course-cell">${coursesTags(s.courses)}<button class="course-edit-btn" data-action="edit" title="コース・月謝・学年を変更">✏️ 変更</button></td>
      <td class="ta-r fee-cell">${yen(s.fee)}</td>
      <td><input type="text" class="email-input" data-action="email" placeholder="未登録" value="${escapeHtml(getEmail(s.id))}"></td>
      <td><input type="text" class="payer-input" data-action="payer" placeholder="—" value="${escapeHtml(getPayerName(s.id))}"></td>
      <td>${statusSelect(s)}</td>
      <td class="ta-c">
        <button class="pay-toggle ${paid ? 'paid' : ''}" data-action="toggle" title="${paid ? '入金済' : '未払い'}">${paid ? '✓' : '○'}</button>
      </td>
      <td class="ta-c">${stripeRegBadge(s)} ${spotChargeBtnForStudent(s)}</td>
    </tr>`;
  }).join('');

  tbody.onclick = (e) => {
    const btn = e.target.closest('[data-action]');
    if (!btn) return;
    const a = btn.dataset.action;
    if (a !== 'toggle' && a !== 'link-reg' && a !== 'unlink-reg' && a !== 'edit' && a !== 'spot-charge') return;  // email/payer/status は oninput/onchange 側で処理
    const tr = btn.closest('tr');
    const id = parseInt(tr.dataset.studentId, 10);
    if (a === 'toggle') {
      const pay = getPayment(month, id);
      const newPaid = !(pay && pay.paid);
      setPayment(month, id, newPaid, newPaid ? new Date().toISOString().slice(0, 10) : '', newPaid ? '手動チェック' : '', null);
      refresh();
    } else if (a === 'link-reg') {
      handleLinkRegClick(id, btn.dataset.regId, btn.dataset.customerId);
    } else if (a === 'unlink-reg') {
      handleUnlinkRegClick(id);
    } else if (a === 'edit') {
      openEditStudentModal(id);
    } else if (a === 'spot-charge') {
      const link = getRegLink(id);
      if (!link || !link.regId) { alert('この生徒はカード未登録のため講習費用の請求はできません。'); return; }
      const nm = (tr.querySelector('.name-cell')?.textContent || `#${id}`).trim();
      openSpotChargeModal(link.regId, nm, link.customerId);
    }
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
  else if (name === 'monthend') renderMonthEnd();
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
  else if (active === 'monthend') renderMonthEnd();
}

// ===========================================================================
// 💳 月末一斉引き落とし (Stripe Setup Mode + 月末バッチ請求) - 2026-05-13
// ===========================================================================
const MONTHEND_STATE = { lastPreview: null, busy: false, excluded: new Set(), includeArrears: false, billMode: 'current', lastLedger: null, ledgerBusy: false };

// 請求対象月ヘルパー (2026-06-26: 月末に翌月分を前倒し請求する運用)。
//   billMode 'current' → カレンダー月 / 'next' → 翌月。
function monthEndCalMonth() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
}
function monthEndAddMonth(ym, delta) {
  let y = parseInt(ym.slice(0, 4), 10), m = parseInt(ym.slice(5, 7), 10) + delta;
  while (m > 12) { m -= 12; y++; }
  while (m <= 0) { m += 12; y--; }
  return `${y}-${String(m).padStart(2, '0')}`;
}
function monthEndTargetMonth() {
  const cal = monthEndCalMonth();
  return MONTHEND_STATE.billMode === 'next' ? monthEndAddMonth(cal, 1) : cal;
}
// プレビューが翌月分モードか (請求対象月 ≠ カレンダー月)。滞納同時請求はこのとき無効化する。
function monthEndIsNextMode(prev) {
  prev = prev || MONTHEND_STATE.lastPreview;
  return !!(prev && prev.current_month && prev.month && prev.month !== prev.current_month);
}

function fmtYenME(n) {
  try { return '¥' + Number(n || 0).toLocaleString('ja-JP'); }
  catch (_) { return '¥' + (n || 0); }
}

// epoch 秒 → JST の "M/D" 表示 (0/不正値は空文字)。台帳の引落日・カード登録日表示用。
function fmtDateME(epochSec) {
  const n = Number(epochSec) || 0;
  if (n <= 0) return '';
  try {
    return new Date(n * 1000).toLocaleDateString('ja-JP', { timeZone: 'Asia/Tokyo', month: 'numeric', day: 'numeric' });
  } catch (_) { return ''; }
}

function getMonthEndAdminPw() {
  // monthend タブ + chat タブの両方でパスワードを共有
  const pw1 = document.getElementById('monthEndAdminPw')?.value?.trim();
  const pw2 = document.getElementById('chatAdminPw')?.value?.trim();
  return pw1 || pw2 || '';
}

function setMonthEndStatus(html, level) {
  const el = document.getElementById('monthEndStatus');
  if (!el) return;
  const colorMap = {
    'info':    'rgba(99,102,241,0.12); border:1px solid rgba(99,102,241,0.3); color:var(--primary-light)',
    'success': 'rgba(16,185,129,0.12); border:1px solid rgba(16,185,129,0.3); color:var(--success)',
    'error':   'rgba(239,68,68,0.12); border:1px solid rgba(239,68,68,0.3); color:#f87171',
    'warn':    'rgba(245,158,11,0.12); border:1px solid rgba(245,158,11,0.3); color:#fbbf24',
  };
  const bg = colorMap[level || 'info'];
  if (!html) { el.innerHTML = ''; el.style.cssText = ''; return; }
  el.innerHTML = html;
  el.style.cssText = `padding:0.75rem 1rem;border-radius:8px;background:${bg};`;
}

async function renderMonthEnd() {
  // タブを開いた直後の初期表示。パスワード入力前は何もしない
  const tag = document.getElementById('monthEndMonthTag');
  if (tag) {
    const now = new Date();
    const y = now.getFullYear();
    const m = String(now.getMonth() + 1).padStart(2, '0');
    tag.textContent = `${y}-${m}`;
  }
  // パスワード自動入力 (chat タブと共有)
  const pwShared = document.getElementById('chatAdminPw')?.value?.trim();
  if (pwShared && !document.getElementById('monthEndAdminPw').value) {
    document.getElementById('monthEndAdminPw').value = pwShared;
  }
}

async function fetchMonthEndPreview() {
  const pw = getMonthEndAdminPw();
  if (!pw) {
    setMonthEndStatus('🔒 管理パスワードを入力してください', 'warn');
    return;
  }
  if (MONTHEND_STATE.busy) return;
  MONTHEND_STATE.busy = true;
  setMonthEndStatus('⏳ プレビュー取得中...', 'info');
  try {
    const res = await fetch('/payment/api/admin-charge-month-end-preview', {
      method: 'GET',
      headers: { 'X-Admin-Password': pw, 'X-Target-Month': monthEndTargetMonth() },
    });
    if (res.status === 401) {
      setMonthEndStatus('❌ 認証失敗。管理パスワードを確認してください', 'error');
      MONTHEND_STATE.busy = false;
      return;
    }
    const data = await res.json();
    if (!res.ok) {
      setMonthEndStatus(`❌ エラー: ${data.message || data.error || 'unknown'}`, 'error');
      MONTHEND_STATE.busy = false;
      return;
    }
    MONTHEND_STATE.lastPreview = data;
    renderMonthEndTable(data);
    setMonthEndStatus(`✅ 月 <strong>${data.month}</strong> のプレビュー取得完了 (${data.total_customers} 名)`, 'success');
    renderUnchargedNote(data);
    fetchChargeLedger();   // 📖 台帳も自動更新 (非同期・失敗してもプレビュー表示には影響しない)
  } catch (e) {
    setMonthEndStatus(`❌ ネットワークエラー: ${e.message}`, 'error');
  } finally {
    MONTHEND_STATE.busy = false;
  }
}

// === 滞納分 (過去の未払い月) 一括引き落とし 用ヘルパー (2026-06-01 塾長要望) ===
// 月文字列 "YYYY-MM" の n ヶ月前リストを返す (新しい順)。
function monthEndPriorMonths(month, n) {
  const out = [];
  const parts = String(month || '').split('-');
  const y = parseInt(parts[0], 10), m = parseInt(parts[1], 10);
  if (!y || !m) return out;
  for (let i = 1; i <= n; i++) {
    let yy = y, mm = m - i;
    while (mm <= 0) { mm += 12; yy -= 1; }
    out.push(`${yy}-${String(mm).padStart(2, '0')}`);
  }
  return out;
}

// プレビュー顧客 c の「滞納分」を返す。紐付け✓確定済み (regLinks) の生徒のみ対象 (曖昧マッチでの誤請求を防ぐ)。
// priorMonths のうち名簿で未払いの月を抽出。滞納なし/未紐付けは null。金額はサーバ側で登録月謝を使うが、
// 表示・集計用に c.monthlyFee を fee として返す。
function monthEndArrearsFor(c, regToStudent, priorMonths) {
  if (!c || !c.ready || c.alreadyChargedThisMonth) return null;
  const sid = regToStudent[c.registrationId];
  if (sid === undefined || sid === null) return null;   // 紐付け未確定 → 滞納対象外
  const months = priorMonths.filter(pm => {
    const pay = getPayment(pm, sid);
    return !(pay && pay.paid);                            // 名簿で未払いの月だけ
  });
  if (!months.length) return null;
  return { studentId: sid, months: months, fee: Number(c.monthlyFee) || 0 };
}

function renderMonthEndTable(data) {
  document.getElementById('monthEndMonthTag').textContent = data.month;
  document.getElementById('monthEndTotalCustomers').textContent = data.total_customers;
  document.getElementById('monthEndAlreadyCount').textContent = data.previously_charged_this_month;
  document.getElementById('monthEndSummary').style.display = '';
  document.getElementById('monthEndActionBar').style.display = 'flex';

  const tbody = document.getElementById('monthEndTbody');
  if (!data.customers || data.customers.length === 0) {
    tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;color:var(--text-dim);padding:2rem">カード登録済の顧客がまだいません</td></tr>';
    updateMonthEndSelectionSummary();
    return;
  }
  const meRegToStudent = buildRegIdToStudentMap();
  const mePriorMonths = monthEndPriorMonths(data.month, 3);
  const rows = data.customers.map(c => {
    let statusBadge = '';
    const chargeable = !!c.ready && !c.alreadyChargedThisMonth;
    if (c.alreadyChargedThisMonth) {
      statusBadge = '<span style="color:var(--text-dim);">✅ 当月引き落とし済</span>';
    } else if (c.ready) {
      statusBadge = '<span style="color:var(--success);">🟢 ready</span>';
      // 未請求の人にはカード登録日を添える (一斉実行のあとに登録した人を見分けるため)
      const regDate = fmtDateME(c.registeredAt);
      if (regDate) {
        statusBadge += `<div style="font-size:0.72rem;color:var(--text-dim);margin-top:2px;white-space:nowrap;">カード登録 ${regDate}</div>`;
      }
    } else {
      statusBadge = `<span style="color:#f87171;">⚠️ ${escapeHtmlME(c.issue || 'NG')}</span>`;
    }
    const rid = escapeHtmlME(c.registrationId);
    // 滞納分の明細 (includeArrears ON ∧ 紐付け✓確定済み ∧ 過去に未払い月あり のとき)
    // 翌月分モードでは滞納同時請求は不可 (誤請求防止) → 明細も出さない。
    let arrearsSub = '';
    if (MONTHEND_STATE.includeArrears && chargeable && !monthEndIsNextMode(data)) {
      const a = monthEndArrearsFor(c, meRegToStudent, mePriorMonths);
      if (a) {
        const lbl = a.months.map(m => `${parseInt(m.slice(5), 10)}月`).join('・');
        arrearsSub = `<div style="font-size:0.74rem;color:#fbbf24;margin-top:3px;white-space:nowrap;">＋滞納 ${lbl} ¥${(a.fee * a.months.length).toLocaleString()}</div>`;
      }
    }
    // 対象トグル: 請求可能な行のみ。OFF (excluded) は一斉実行の対象から外れる (サーバ側でも除外を強制)。
    const toggleCell = chargeable
      ? `<td class="ta-c"><input type="checkbox" class="me-toggle" ${MONTHEND_STATE.excluded.has(c.registrationId) ? '' : 'checked'} onchange="toggleMonthEndRow('${rid}', this.checked)" title="今回の一斉引き落としの対象にする / 外す" style="width:18px;height:18px;cursor:pointer;"></td>`
      : `<td class="ta-c" style="color:var(--text-dim)">—</td>`;
    // 個別請求 (この人だけ) + 退塾。一斉実行のあとにカード登録した人の追い請求もこのボタン。
    const oneBtn = chargeable
      ? `<button class="btn btn-ghost btn-sm" onclick="chargeOneMonthEnd('${rid}')" title="この人だけ今すぐ引き落とし (一斉実行後にカード登録した人の請求もこれでOK)" style="color:#34d399;border-color:rgba(16,185,129,0.45);">💳 個別請求</button> `
      : '';
    // 🎓 講習費用の単発スポット課金 (任意金額・1回限り・月謝は変えない)。カード紐付け(ready)なら当月請求済でも可。
    const spotBtn = c.ready
      ? `<button class="btn btn-ghost btn-sm" onclick="chargeSpotFor('${rid}')" title="講習費用などを任意金額で今すぐ1回だけ請求 (月謝は変わりません)" style="color:#a78bfa;border-color:rgba(139,92,246,0.45);">🎓 講習費用</button> `
      : '';
    return `<tr>
      ${toggleCell}
      <td>${escapeHtmlME(c.studentName)}</td>
      <td>${escapeHtmlME(c.grade)}</td>
      <td>${escapeHtmlME(c.parentName)}</td>
      <td style="font-size:0.85rem">${escapeHtmlME(c.email)}</td>
      <td class="ta-r"><strong>${fmtYenME(c.monthlyFee)}</strong>${arrearsSub}</td>
      <td style="font-size:0.85rem;color:var(--text-dim)">${escapeHtmlME(c.feeBreakdown)}</td>
      <td>${statusBadge}</td>
      <td style="white-space:nowrap">${oneBtn}${spotBtn}<button class="btn btn-ghost btn-sm" onclick="cancelRegistration('${rid}', '${escapeHtmlME(c.studentName)}')" style="color:#f87171" title="退塾処理">🗑</button></td>
    </tr>`;
  }).join('');
  tbody.innerHTML = rows;
  updateMonthEndSelectionSummary();
}

// 対象トグル ON/OFF → excluded セット更新 + 集計再計算 (2026-06-01: 塾長要望の引き落としスイッチ)
function toggleMonthEndRow(rid, checked) {
  if (!rid) return;
  if (checked) MONTHEND_STATE.excluded.delete(rid);
  else MONTHEND_STATE.excluded.add(rid);
  updateMonthEndSelectionSummary();
}
window.toggleMonthEndRow = toggleMonthEndRow;

// 一斉実行の対象 rid (ready ∧ 当月未請求 ∧ トグル ON) の配列。これだけをサーバに送る。
function selectedMonthEndIds() {
  const prev = MONTHEND_STATE.lastPreview;
  if (!prev || !Array.isArray(prev.customers)) return [];
  return prev.customers
    .filter(c => c.ready && !c.alreadyChargedThisMonth && !MONTHEND_STATE.excluded.has(c.registrationId))
    .map(c => c.registrationId)
    .filter(Boolean);
}

// サマリーカード「引き落とし可能 / 合計引き落とし額」を選択中の人数・合計で更新 (= 実行で実際に請求される額)
function updateMonthEndSelectionSummary() {
  const prev = MONTHEND_STATE.lastPreview;
  const cntEl = document.getElementById('monthEndReadyCount');
  const amtEl = document.getElementById('monthEndTotalAmount');
  if (!prev || !Array.isArray(prev.customers)) return;
  const chargeable = prev.customers.filter(c => c.ready && !c.alreadyChargedThisMonth);
  const sel = chargeable.filter(c => !MONTHEND_STATE.excluded.has(c.registrationId));
  const curSum = sel.reduce((a, c) => a + (Number(c.monthlyFee) || 0), 0);
  // 滞納分の合計 (includeArrears ON のとき・選択中の人のみ)。実行で実際に請求される総額に反映。
  // 翌月分モードでは滞納同時請求は不可のため合計に含めない。
  let arrearsSum = 0;
  if (MONTHEND_STATE.includeArrears && !monthEndIsNextMode(prev)) {
    const regToStudent = buildRegIdToStudentMap();
    const priorMonths = monthEndPriorMonths(prev.month, 3);
    for (const c of sel) {
      const a = monthEndArrearsFor(c, regToStudent, priorMonths);
      if (a) arrearsSum += a.fee * a.months.length;
    }
  }
  const total = curSum + arrearsSum;
  if (cntEl) {
    cntEl.innerHTML = (sel.length < chargeable.length)
      ? `${sel.length}<span style="font-size:0.5em;color:var(--text-dim);font-weight:400;"> / ${chargeable.length} 名を選択中</span>`
      : `${sel.length}`;
  }
  if (amtEl) {
    amtEl.innerHTML = (arrearsSum > 0)
      ? `${fmtYenME(total)}<span style="font-size:0.5em;color:#fbbf24;font-weight:400;"> (当月 ${fmtYenME(curSum)} ＋滞納 ${fmtYenME(arrearsSum)})</span>`
      : fmtYenME(total);
  }
}

// 💡 「一斉実行のあとにカード登録した人」を目立たせるバナー。
// 請求対象月で誰かに請求済み (previously_charged_this_month > 0) なのに未請求 ready が残っている時だけ表示
// (月初〜一斉実行前の「全員未請求」の状態ではうるさいので出さない)。
function renderUnchargedNote(data) {
  const el = document.getElementById('monthEndUnchargedNote');
  if (!el) return;
  const uncharged = ((data && data.customers) || []).filter(c => c.ready && !c.alreadyChargedThisMonth);
  if (!(data && data.previously_charged_this_month > 0) || uncharged.length === 0) {
    el.style.display = 'none';
    el.innerHTML = '';
    return;
  }
  const MAX_NAMES = 8;
  const names = uncharged.slice(0, MAX_NAMES).map(c => {
    const d = fmtDateME(c.registeredAt);
    return `<strong>${escapeHtmlME(c.studentName || '(名前未設定)')}</strong>${d ? `<span style="font-size:0.78rem;">（カード登録 ${d}）</span>` : ''}`;
  }).join('・') + (uncharged.length > MAX_NAMES ? ` ほか ${uncharged.length - MAX_NAMES} 名` : '');
  el.innerHTML = `💡 <strong>${escapeHtmlME(data.month)} 分をまだ引き落とせていない</strong>カード登録者が ${uncharged.length} 名います: ${names}<br>
    <span style="font-size:0.82rem;color:var(--text-dim);">一斉実行のあとにカード登録した生徒のほか、引き落とし失敗・対象トグルOFFで外した生徒もここに出ます。表か下の📖台帳の「💳 個別請求」でその人の分だけ請求できます (他の人に請求は飛びません)。</span>`;
  el.style.cssText = 'margin-bottom:1rem;display:block;padding:0.75rem 1rem;border-radius:8px;background:rgba(245,158,11,0.10);border:1px solid rgba(245,158,11,0.35);color:#fbbf24;';
}

// 「💳 個別請求 (この人だけ)」個別引き落とし。同じ execute エンドポイントに registrationIds:[rid] を渡す
// (サーバ側で当月二重請求は SET NX で防止済み)。
// expectedMonth (任意): 📖台帳のマスから呼ぶ時にマスの月を焼き込む。プレビューの請求対象月と
// 一致しない (モード切替直後の stale 表示など) 場合は請求せず中止する (2026-07-02 review)。
async function chargeOneMonthEnd(rid, expectedMonth) {
  if (MONTHEND_STATE.busy) return;
  const pw = getMonthEndAdminPw();
  if (!pw) { setMonthEndStatus('🔒 管理パスワードを入力してください', 'warn'); return; }
  const preview = MONTHEND_STATE.lastPreview;
  if (!preview) { setMonthEndStatus('⚠️ 先に「🔄 プレビュー更新」を押してください', 'warn'); return; }
  const c = (preview.customers || []).find(x => x.registrationId === rid);
  if (!c) { setMonthEndStatus('対象が見つかりません。「🔄 プレビュー更新」を押してください', 'warn'); return; }
  if (!c.ready || c.alreadyChargedThisMonth) { setMonthEndStatus('この人は請求対象外です (未 ready または当月請求済)', 'warn'); return; }
  const nowMonth = monthEndCalMonth();
  const calMonth = preview.current_month || preview.month;   // カレンダー月 (confirmMonth ガード用)
  const billMonth = preview.month;                           // 請求対象月 (今月 or 翌月)
  const isNextMonth = billMonth !== calMonth;
  if (calMonth !== nowMonth) {
    setMonthEndStatus(`⚠️ プレビューの基準月 (${calMonth}) と現在月 (${nowMonth}) が不一致。「🔄 プレビュー更新」を押してください`, 'error');
    return;
  }
  if (expectedMonth && expectedMonth !== billMonth) {
    setMonthEndStatus(`⚠️ このボタンは ${expectedMonth} 分ですが、現在の請求対象月は ${billMonth} です (表示が古い可能性)。「🔄 プレビュー更新」してからやり直してください`, 'warn');
    return;
  }
  // 一斉実行と同じ鮮度ガード: プレビューが10分以上前なら中止 (2026-07-02 review)
  const previewAge = Date.now() / 1000 - (preview.preview_at || 0);
  if (previewAge > 600) {
    setMonthEndStatus(`⚠️ プレビューが古いです (${Math.floor(previewAge / 60)} 分前)。「🔄 プレビュー更新」を押してからやり直してください`, 'warn');
    return;
  }
  const amt = Number(c.monthlyFee) || 0;
  if (!confirm(`💳 ${c.studentName} さん 1 名だけを今すぐ引き落とします。\n\n金額: ${fmtYenME(amt)}\n請求月: ${billMonth}${isNextMonth ? ' (翌月分)' : ''}\n\n実行後は取り消せません。よろしいですか?`)) return;
  MONTHEND_STATE.busy = true;
  setMonthEndStatus(`⏳ ${c.studentName} さんを引き落とし中...`, 'info');
  try {
    const body = { dryRun: false, confirmMonth: calMonth, registrationIds: [rid] };
    if (isNextMonth) body.chargeMonth = billMonth;   // 翌月分の前倒し請求
    const res = await fetch('/payment/api/admin-charge-month-end-execute', {
      method: 'POST',
      headers: { 'X-Admin-Password': pw, 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) { setMonthEndStatus(`❌ 実行エラー: ${data.message || data.error || 'unknown'}`, 'error'); MONTHEND_STATE.busy = false; return; }
    showMonthEndResultModal(data, false);
    setTimeout(() => fetchMonthEndPreview(), 500);
  } catch (e) {
    setMonthEndStatus(`❌ ネットワークエラー: ${e.message}`, 'error');
  } finally {
    MONTHEND_STATE.busy = false;
  }
}
window.chargeOneMonthEnd = chargeOneMonthEnd;

// 🎓 講習費用の単発スポット課金。月謝(monthly_fee)は変えず、保存カードに任意金額を1回だけ即時引落。
//   専用エンドポイント /payment/api/admin-charge-spot を叩く (月末バッチの done_key とは別ロック)。
// 月末タブの行内🎓ボタン → 専用モーダルを開く (prompt 廃止)。カード紐付け(ready)のみ。
function chargeSpotFor(rid) {
  const preview = MONTHEND_STATE.lastPreview;
  if (!preview) { setMonthEndStatus('⚠️ 先に「🔄 プレビュー更新」を押してください', 'warn'); return; }
  const c = (preview.customers || []).find(x => x.registrationId === rid);
  if (!c) { setMonthEndStatus('対象が見つかりません。「🔄 プレビュー更新」を押してください', 'warn'); return; }
  if (!c.ready) { setMonthEndStatus('この生徒はカード即時引落の対象外です (カード未登録/不備)', 'warn'); return; }
  openSpotChargeModal(rid, c.studentName, c.customerId);
}
window.chargeSpotFor = chargeSpotFor;

// === 🎓 講習費用 専用モーダル (月末タブ/生徒一覧 両導線の共通UI・常設の金額入力欄) ===
function setSpotChargeStatus(html, level) {
  const el = document.getElementById('spotChargeStatus');
  if (!el) return;
  const colorMap = { info: '#a5b4fc', success: '#34d399', error: '#f87171', warn: '#fbbf24' };
  if (!html) { el.innerHTML = ''; el.style.cssText = 'font-size:0.84rem;'; return; }
  el.innerHTML = html;
  el.style.cssText = `font-size:0.84rem;font-weight:600;line-height:1.4;color:${colorMap[level || 'info']};`;
}

// rid(reg_xxx) が無い=カード未登録は開けない (呼び出し側でガード済みだが二重に防止)
function openSpotChargeModal(rid, studentName, customerId) {
  if (!rid) { alert('この生徒はカード未登録のため講習費用のカード請求はできません。先にカード紐付けが必要です。'); return; }
  const m = document.getElementById('spotChargeModal');
  if (!m) return;
  document.getElementById('spotChargeRid').value = rid;
  document.getElementById('spotChargeStudentName').textContent = studentName || '(氏名不明)';
  document.getElementById('spotChargeInfo').textContent = customerId ? `Stripe: ${customerId} / ${rid}` : rid;
  document.getElementById('spotChargeAmount').value = '';
  document.getElementById('spotChargeLabel').value = '講習費用';
  document.getElementById('spotChargePw').value = getMonthEndAdminPw() || '';
  setSpotChargeStatus('', '');
  const btn = document.getElementById('spotChargeSubmitBtn');
  if (btn) { btn.disabled = false; btn.style.opacity = ''; }
  m.classList.remove('hidden');
  m.style.display = '';
  setTimeout(() => { try { document.getElementById('spotChargeAmount').focus(); } catch (_) {} }, 50);
}
window.openSpotChargeModal = openSpotChargeModal;

function closeSpotChargeModal() {
  const m = document.getElementById('spotChargeModal');
  if (!m) return;
  m.classList.add('hidden');
  m.style.display = 'none';
}
window.closeSpotChargeModal = closeSpotChargeModal;

let SPOT_CHARGE_BUSY = false;
async function submitSpotCharge() {
  if (SPOT_CHARGE_BUSY) return;
  const rid = document.getElementById('spotChargeRid').value;
  const studentName = (document.getElementById('spotChargeStudentName').textContent || '').trim();
  const pw = (document.getElementById('spotChargePw').value || '').trim();
  const label = (document.getElementById('spotChargeLabel').value || '講習費用').trim() || '講習費用';
  const amt = parseInt(String(document.getElementById('spotChargeAmount').value).replace(/[^0-9]/g, ''), 10);
  if (!rid) { setSpotChargeStatus('対象が不正です。画面を再読込してください。', 'error'); return; }
  if (!pw) { setSpotChargeStatus('🔒 管理パスワードを入力してください', 'warn'); return; }
  if (!amt || amt < 1000 || amt > 500000) { setSpotChargeStatus('⚠️ 金額は 1,000〜500,000 円で入力してください', 'error'); return; }
  if (!confirm(`💳 ${studentName} さんのカードに\n\n　${label}: ${fmtYenME(amt)}\n\nを今すぐ請求します。実行後は取り消せません。よろしいですか?`)) return;
  // 二重押下防止トークン (確認ごとに一意。サーバ側 SET NX + Stripe Idempotency-Key で二重課金防止)
  const idemToken = `spot-${rid}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  SPOT_CHARGE_BUSY = true;
  const btn = document.getElementById('spotChargeSubmitBtn');
  if (btn) { btn.disabled = true; btn.style.opacity = '0.5'; }
  setSpotChargeStatus(`⏳ ${studentName} さんに ${label} ${fmtYenME(amt)} を請求中...`, 'info');
  try {
    const res = await fetch('/payment/api/admin-charge-spot', {
      method: 'POST',
      headers: { 'X-Admin-Password': pw, 'Content-Type': 'application/json' },
      body: JSON.stringify({ registrationId: rid, amount: amt, label, idemToken }),
    });
    const data = await res.json();
    if (!res.ok) { setSpotChargeStatus(`❌ 実行エラー: ${data.message || data.error || 'unknown'}`, 'error'); return; }
    if (data.status === 'success') {
      setSpotChargeStatus(`✅ ${data.studentName} さんに ${label} ${fmtYenME(data.amount)} を請求しました (${data.paymentIntentId})`, 'success');
      // 月末プレビューが開いていれば最新化 (spot は月謝に非干渉だが履歴反映のため)
      if (MONTHEND_STATE.lastPreview && typeof fetchMonthEndPreview === 'function') { try { fetchMonthEndPreview(); } catch (_) {} }
    } else if (data.status === 'requires_action') {
      setSpotChargeStatus(`🔐 ${data.studentName} さん: カード会社の3DS本人確認が必要です。確認後に課金が確定します`, 'warn');
    } else if (data.status === 'uncertain') {
      setSpotChargeStatus(`⚠️ 課金有無が不明です。Stripe Dashboard で確認してください: ${data.error || ''}`, 'error');
    } else {
      setSpotChargeStatus(`❌ 請求失敗: ${data.error || data.declineCode || data.errorCode || 'unknown'}`, 'error');
    }
  } catch (e) {
    setSpotChargeStatus(`❌ ネットワークエラー: ${e.message}`, 'error');
  } finally {
    SPOT_CHARGE_BUSY = false;
    if (btn) { btn.disabled = false; btn.style.opacity = ''; }
  }
}
window.submitSpotCharge = submitSpotCharge;

function escapeHtmlME(s) {
  // シングルクォートも潰す: onclick="fn('...')" のような単引用符コンテキストに埋め込むため
  // (rid はサーバ生成 token_urlsafe で通常混入しないが、構造的防御・2026-07-02 review)
  return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

// 月末 execute エンドポイントへの単一 POST (当月 or 滞納月)。
async function postMonthEndExecuteCall(pw, body) {
  const res = await fetch('/payment/api/admin-charge-month-end-execute', {
    method: 'POST',
    headers: { 'X-Admin-Password': pw, 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  return { ok: res.ok, data };
}

// 実請求 (dry-run でない) の success を名簿に「入金済」反映 (紐付け✓確定済み生徒のみ)。
// カード引落と名簿が連動していなかったギャップ (二重徴収リスク) もこれで解消。
function markMonthEndChargedPaid(month, results, regToStudent) {
  let n = 0;
  const today = new Date().toISOString().slice(0, 10);
  for (const r of (results || [])) {
    if (r.status !== 'success') continue;
    const sid = regToStudent[r.registrationId];
    if (sid === undefined || sid === null) continue;
    const pay = getPayment(month, sid);
    if (pay && pay.paid) continue;
    setPayment(month, sid, true, today, `カード引落 ${month}`, Number(r.amount) || null);
    n++;
  }
  return n;
}

async function executeMonthEndCharge(dryRun) {
  if (MONTHEND_STATE.busy) return;
  const pw = getMonthEndAdminPw();
  if (!pw) { setMonthEndStatus('🔒 管理パスワードを入力してください', 'warn'); return; }
  const preview = MONTHEND_STATE.lastPreview;
  if (!preview) { setMonthEndStatus('⚠️ 先に「🔄 プレビュー更新」を押してください', 'warn'); return; }

  // 🚨 freshness check: preview が 10 分以上前 or 月が変わっている場合は再取得を強制
  const previewAge = Date.now() / 1000 - (preview.preview_at || 0);
  const nowMonth = monthEndCalMonth();
  const calMonth = preview.current_month || preview.month;   // サーバのカレンダー月 (confirmMonth ガード用)
  const billMonth = preview.month;                           // 請求対象月 (今月 or 翌月)
  const isNextMonth = billMonth !== calMonth;
  if (calMonth !== nowMonth) {
    setMonthEndStatus(`⚠️ プレビューの基準月 (${calMonth}) と現在月 (${nowMonth}) が一致しません。「🔄 プレビュー更新」を押してください`, 'error');
    return;
  }
  if (previewAge > 600 && !dryRun) {
    setMonthEndStatus(`⚠️ プレビューが古いです (${Math.floor(previewAge / 60)} 分前)。再度「🔄 プレビュー更新」を押してください`, 'warn');
    return;
  }

  const month = billMonth;   // 表示・名簿反映ラベルは請求対象月

  // 対象トグルで選択された人だけを請求 (ready ∧ 当月未請求 ∧ ON)。0 名なら必ず中止 (空配列を送らない)。
  const selectedIds = selectedMonthEndIds();
  if (selectedIds.length === 0) {
    setMonthEndStatus('⚠️ 対象が 0 名です (対象トグルが全て OFF か、請求可能な人がいません)。1 名以上を ON にしてください', 'warn');
    return;
  }
  const selSet = new Set(selectedIds);
  const selCustomers = (preview.customers || []).filter(c => selSet.has(c.registrationId));
  const selTotal = selCustomers.reduce((a, c) => a + (Number(c.monthlyFee) || 0), 0);

  // === 滞納分の計画 (includeArrears ON のとき・紐付け✓確定済みの選択中生徒のみ) ===
  const regToStudent = buildRegIdToStudentMap();
  const priorMonths = monthEndPriorMonths(month, 3);
  const arrearsPlan = {};            // { "YYYY-MM": [registrationId, ...] }
  const arrearsLines = [];
  let arrearsTotal = 0;
  if (MONTHEND_STATE.includeArrears && !isNextMonth) {
    for (const c of selCustomers) {
      const a = monthEndArrearsFor(c, regToStudent, priorMonths);
      if (!a) continue;
      for (const pm of a.months) {
        (arrearsPlan[pm] = arrearsPlan[pm] || []).push(c.registrationId);
        arrearsTotal += a.fee;
      }
      arrearsLines.push(`  • ${c.studentName}: ${a.months.map(m => `${parseInt(m.slice(5), 10)}月`).join('・')} (¥${(a.fee * a.months.length).toLocaleString()})`);
    }
  }
  const grandTotal = selTotal + arrearsTotal;

  if (!dryRun) {
    const arrearsMsg = (MONTHEND_STATE.includeArrears && arrearsTotal > 0)
      ? `\n\n🕒 滞納分 (過去最大3ヶ月): ¥${arrearsTotal.toLocaleString()}\n${arrearsLines.slice(0, 10).join('\n')}${arrearsLines.length > 10 ? `\n  ...他 ${arrearsLines.length - 10} 名` : ''}\n合計 (当月＋滞納): ¥${grandTotal.toLocaleString()}`
      : '';
    const billLabel = isNextMonth ? `翌月分 (${month})` : `当月 (${month})`;
    const msg = `🚨 本当に実行しますか?\n\n${billLabel}: ${selectedIds.length} 名 / ¥${selTotal.toLocaleString()}${arrearsMsg}\n\n(対象トグル OFF の人・既に引落済みの月は自動で除外されます)\n実行後は取り消せません。`;
    if (!confirm(msg)) return;
    // 2 回目の確認: 請求対象月を手動で入力させて typo 防止
    const typed = prompt(`安全のため、請求対象月を入力してください (例: ${month}) して OK を押してください。\nキャンセルで中止できます。`);
    if (typed === null) return;
    if ((typed || '').trim() !== month) {
      alert(`入力 (${typed}) が請求対象月 (${month}) と一致しません。中止します。`);
      return;
    }
  }
  MONTHEND_STATE.busy = true;
  setMonthEndStatus(dryRun ? '⏳ ドライラン実行中...' : '⏳ 一斉引き落とし実行中... (数分かかる場合があります)', 'info');
  try {
    // 請求コール一覧: 請求対象月 (registrationIds) + 滞納各月 (chargeMonth + その月を未払いの生徒)。各月 1 コール。
    // 翌月分モードでは main コールに chargeMonth=翌月 を渡してその月で請求する (滞納は同時不可)。
    const calls = [{ month: billMonth, ids: selectedIds, arrears: false, chargeMonth: isNextMonth ? billMonth : null }];
    if (MONTHEND_STATE.includeArrears && !isNextMonth) {
      for (const pm of priorMonths) {
        const ids = arrearsPlan[pm];
        if (ids && ids.length) calls.push({ month: pm, ids: ids, arrears: true });
      }
    }
    const agg = {
      month: month,
      dry_run: dryRun,   // 結果CSVのファイル名ラベル (dryrun/live) を正しくするため
      summary: { total: 0, success: 0, failed: 0, skipped: 0, total_amount_charged: 0 },
      results: [],
    };
    let writeBackN = 0;
    let lastError = '';
    for (const call of calls) {
      // confirmMonth は常にカレンダー月 (サーバの MONTH_MISMATCH ガード用)。
      // chargeMonth で実際の請求対象月を指定 (滞納=過去月 / 翌月前倒し=翌月)。
      const body = { dryRun: dryRun, confirmMonth: calMonth, registrationIds: call.ids };
      if (call.arrears) body.chargeMonth = call.month;            // 滞納月 (過去・サーバ側で範囲検証)
      else if (call.chargeMonth) body.chargeMonth = call.chargeMonth;  // 翌月分の前倒し請求
      const { ok, data } = await postMonthEndExecuteCall(pw, body);
      if (!ok) { lastError = data.message || data.error || 'unknown'; continue; }
      const s = data.summary || {};
      agg.summary.total += s.total || 0;
      agg.summary.success += s.success || 0;
      agg.summary.failed += s.failed || 0;
      agg.summary.skipped += s.skipped || 0;
      agg.summary.total_amount_charged += s.total_amount_charged || 0;
      for (const r of (data.results || [])) {
        agg.results.push(call.arrears
          ? Object.assign({}, r, { studentName: `[${parseInt(call.month.slice(5), 10)}月分] ${r.studentName || r.registrationId}` })
          : r);
      }
      if (!dryRun) writeBackN += markMonthEndChargedPaid(call.month, data.results, regToStudent);
    }
    if (lastError && agg.results.length === 0) {
      setMonthEndStatus(`❌ 実行エラー: ${lastError}`, 'error');
      MONTHEND_STATE.busy = false;
      return;
    }
    showMonthEndResultModal(agg, dryRun);
    if (!dryRun) {
      // プレビュー再取得 (already_charged 反映) + 名簿への入金反映を他タブにも反映
      setTimeout(() => fetchMonthEndPreview(), 500);
    }
  } catch (e) {
    setMonthEndStatus(`❌ ネットワークエラー: ${e.message}`, 'error');
  } finally {
    MONTHEND_STATE.busy = false;
  }
}

function showMonthEndResultModal(data, dryRun) {
  // 結果を STATE に保存 (CSV エクスポート用)
  MONTHEND_STATE.lastResult = data;
  const modal = document.getElementById('monthEndResultModal');
  const title = document.getElementById('monthEndResultTitle');
  const body = document.getElementById('monthEndResultBody');
  title.textContent = dryRun ? '📊 ドライラン結果' : '✅ 実行結果';
  const s = data.summary || {};
  let html = `
    <div style="margin-bottom:1rem;padding:1rem;background:rgba(99,102,241,0.08);border-radius:8px;">
      <strong>月: ${data.month}</strong> ${dryRun ? '(ドライラン)' : ''}<br>
      対象 <strong>${s.total || 0}</strong> 名・成功 <span style="color:var(--success)"><strong>${s.success || 0}</strong></span>・失敗 <span style="color:#f87171"><strong>${s.failed || 0}</strong></span>・skip <span style="color:var(--text-dim)"><strong>${s.skipped || 0}</strong></span><br>
      合計引き落とし額: <strong style="color:var(--primary-light)">${fmtYenME(s.total_amount_charged || 0)}</strong>
    </div>
    <div style="margin-bottom:0.5rem;display:flex;gap:0.5rem;">
      <button type="button" class="btn btn-ghost btn-sm" id="monthEndResultCsvBtn">📥 結果 CSV ダウンロード</button>
    </div>
  `;
  if (data.results && data.results.length) {
    html += '<table class="table" style="margin-top:0.5rem"><thead><tr><th>生徒名</th><th>メール</th><th>電話</th><th class="ta-r">金額</th><th>状態</th><th>詳細 / 対応</th></tr></thead><tbody>';
    for (const r of data.results) {
      let badge = '';
      let rowStyle = '';
      if (r.status === 'success' || r.status === 'dry_run') badge = '<span style="color:var(--success)">✅ ' + r.status + '</span>';
      else if (r.status === 'failed') { badge = '<span style="color:#f87171">❌ failed</span>'; rowStyle = 'background:rgba(239,68,68,0.06);'; }
      else if (r.status === 'requires_action') { badge = '<span style="color:#fbbf24">🔐 3DS 認証要</span>'; rowStyle = 'background:rgba(245,158,11,0.06);'; }
      else if (r.status === 'uncertain') { badge = '<span style="color:#fbbf24">⚠️ 不確定 (要確認)</span>'; rowStyle = 'background:rgba(245,158,11,0.12);'; }
      else if (r.status === 'skipped') badge = '<span style="color:var(--text-dim)">⏭ skipped</span>';
      const detail = r.error || r.reason || r.paymentIntentId || '';
      const email = r.email || '';
      const phone = r.phone || '';
      html += `<tr style="${rowStyle}">
        <td>${escapeHtmlME(r.studentName || r.registrationId)}</td>
        <td style="font-size:0.82rem">${escapeHtmlME(email)}</td>
        <td style="font-size:0.82rem">${escapeHtmlME(phone)}</td>
        <td class="ta-r">${fmtYenME(r.amount || 0)}</td>
        <td>${badge}</td>
        <td style="font-size:0.82rem;color:var(--text-dim);max-width:280px;word-break:break-word;">${escapeHtmlME(detail)}</td>
      </tr>`;
    }
    html += '</tbody></table>';
  }
  body.innerHTML = html;
  modal.classList.remove('hidden');
  modal.style.display = 'flex';
  // 結果 CSV ボタン bind
  document.getElementById('monthEndResultCsvBtn')?.addEventListener('click', downloadMonthEndResultCsv);
}

// ===========================================================================
// 📜 履歴・失敗者一覧・要対応・退塾処理 (2026-05-13 2nd review 反映)
// ===========================================================================

async function fetchChargeHistory() {
  const pw = getMonthEndAdminPw();
  if (!pw) { setMonthEndStatus('🔒 管理パスワードを入力してください', 'warn'); return; }
  const monthInput = document.getElementById('historyMonthInput').value;
  const month = monthInput || (new Date()).toISOString().slice(0, 7);
  const type = document.getElementById('historyTypeFilter').value || 'all';
  const statusEl = document.getElementById('historyStatus');
  statusEl.innerHTML = '<span style="color:var(--text-dim)">⏳ 取得中...</span>';
  try {
    const res = await fetch(`/payment/api/admin-charge-history?month=${encodeURIComponent(month)}&type=${encodeURIComponent(type)}`, {
      method: 'GET', headers: { 'X-Admin-Password': pw },
    });
    if (res.status === 401) { statusEl.innerHTML = '<span style="color:#f87171">❌ 認証失敗</span>'; return; }
    const data = await res.json();
    if (!res.ok) { statusEl.innerHTML = `<span style="color:#f87171">❌ ${data.message || data.error}</span>`; return; }
    MONTHEND_STATE.lastHistory = data;
    renderChargeHistory(data, type);
    statusEl.innerHTML = `<span style="color:var(--success)">✅ ${month} 取得完了</span>`;
  } catch (e) {
    statusEl.innerHTML = `<span style="color:#f87171">❌ ${e.message}</span>`;
  }
}

function renderChargeHistory(data, filterType) {
  const s = data.summary || {};
  const target = document.getElementById('historyResults');
  let html = `
    <div style="display:flex;gap:0.5rem;flex-wrap:wrap;margin-bottom:0.75rem;">
      <span class="count-tag" style="background:rgba(16,185,129,0.15);color:var(--success);">成功: ${s.success_count || 0}</span>
      <span class="count-tag" style="background:rgba(239,68,68,0.15);color:#f87171;">失敗: ${s.failed_count || 0}</span>
      <span class="count-tag" style="background:rgba(245,158,11,0.15);color:#fbbf24;">3DS要: ${s.requires_action_count || 0}</span>
      <span class="count-tag" style="background:rgba(245,158,11,0.25);color:#fbbf24;">不確定: ${s.uncertain_count || 0}</span>
      <span class="count-tag" style="background:rgba(99,102,241,0.15);color:var(--primary-light);">合計引落額: ${fmtYenME(s.total_amount_charged || 0)}</span>
    </div>
  `;
  // ⚠️ uncertain (最重要・手動 reconcile が必要)
  if ((filterType === 'all' || filterType === 'uncertain') && data.uncertain && data.uncertain.length) {
    html += '<h3 style="margin-top:1rem;color:#fbbf24;">⚠️ 不確定 (timeout) — 要手動確認</h3>';
    html += '<div class="hint" style="font-size:0.85rem;margin-bottom:0.5rem;">Stripe Dashboard で実際の状態を確認後、下のボタンで状態を確定してください</div>';
    html += '<table class="table"><thead><tr><th>生徒名</th><th>メール</th><th>電話</th><th class="ta-r">金額</th><th>Idempotency Key</th><th>操作</th></tr></thead><tbody>';
    for (const r of data.uncertain) {
      html += `<tr>
        <td>${escapeHtmlME(r.studentName)}</td>
        <td style="font-size:0.82rem">${escapeHtmlME(r.email)}</td>
        <td style="font-size:0.82rem">${escapeHtmlME(r.phone)}</td>
        <td class="ta-r">${fmtYenME(r.amount)}</td>
        <td style="font-size:0.7rem;font-family:monospace;word-break:break-all;max-width:200px">${escapeHtmlME(r.idempotencyKey)}</td>
        <td>
          <button class="btn btn-ghost btn-sm" onclick="openReconcileModal('${escapeHtmlME(r.registrationId)}', '${escapeHtmlME(data.month)}', '${escapeHtmlME(r.studentName)}', ${r.amount})">🔧 確定</button>
        </td>
      </tr>`;
    }
    html += '</tbody></table>';
  }
  // 失敗 (再請求可能)
  if ((filterType === 'all' || filterType === 'failed') && data.failed && data.failed.length) {
    html += '<h3 style="margin-top:1rem;color:#f87171;">❌ 失敗 (個別再請求可能)</h3>';
    html += '<table class="table"><thead><tr><th>生徒名</th><th>メール</th><th>電話</th><th class="ta-r">金額</th><th>エラー</th><th>操作</th></tr></thead><tbody>';
    for (const r of data.failed) {
      html += `<tr>
        <td>${escapeHtmlME(r.studentName)}</td>
        <td style="font-size:0.82rem">${escapeHtmlME(r.email)}</td>
        <td style="font-size:0.82rem">${escapeHtmlME(r.phone)}</td>
        <td class="ta-r">${fmtYenME(r.amount)}</td>
        <td style="font-size:0.82rem;color:var(--text-dim);max-width:250px;word-break:break-word">${escapeHtmlME(r.errorCode || '')} / ${escapeHtmlME(r.declineCode || '')}<br>${escapeHtmlME(r.errorDetail || '').substring(0, 100)}</td>
        <td>
          <button class="btn btn-ghost btn-sm" onclick="retryCharge('${escapeHtmlME(r.registrationId)}', '${escapeHtmlME(data.month)}', '${escapeHtmlME(r.studentName)}', ${r.amount})">🔁 再請求</button>
        </td>
      </tr>`;
    }
    html += '</tbody></table>';
  }
  // 3DS 要
  if ((filterType === 'all' || filterType === 'requires_action') && data.requires_action && data.requires_action.length) {
    html += '<h3 style="margin-top:1rem;color:#fbbf24;">🔐 3DS 認証要</h3>';
    html += '<table class="table"><thead><tr><th>生徒名</th><th>メール</th><th class="ta-r">金額</th><th>確認URL</th></tr></thead><tbody>';
    for (const r of data.requires_action) {
      const link = r.redirectUrl ? `<a href="${escapeHtmlME(r.redirectUrl)}" target="_blank" rel="noopener" style="color:var(--primary-light)">🔗 顧客に送る URL</a>` : '<span style="color:var(--text-dim)">URL なし</span>';
      html += `<tr>
        <td>${escapeHtmlME(r.studentName)}</td>
        <td style="font-size:0.82rem">${escapeHtmlME(r.email)}</td>
        <td class="ta-r">${fmtYenME(r.amount)}</td>
        <td style="font-size:0.82rem">${link}</td>
      </tr>`;
    }
    html += '</tbody></table>';
  }
  // 成功
  if ((filterType === 'all' || filterType === 'success') && data.success && data.success.length) {
    html += `<h3 style="margin-top:1rem;color:var(--success);">✅ 成功 (${data.success.length} 名)</h3>`;
    html += '<table class="table"><thead><tr><th>生徒名</th><th>メール</th><th class="ta-r">金額</th><th>PaymentIntentId</th><th>日時</th></tr></thead><tbody>';
    for (const r of data.success) {
      const dt = r.chargedAt ? new Date(r.chargedAt * 1000).toLocaleString('ja-JP') : '';
      html += `<tr>
        <td>${escapeHtmlME(r.studentName)}</td>
        <td style="font-size:0.82rem">${escapeHtmlME(r.email)}</td>
        <td class="ta-r">${fmtYenME(r.amount)}</td>
        <td style="font-size:0.7rem;font-family:monospace">${escapeHtmlME(r.paymentIntentId)}</td>
        <td style="font-size:0.82rem">${escapeHtmlME(dt)}</td>
      </tr>`;
    }
    html += '</tbody></table>';
  }
  target.innerHTML = html;
}

// 📥 履歴 CSV
function downloadHistoryCsv() {
  const data = MONTHEND_STATE.lastHistory;
  if (!data) return;
  const rows = [['月','状態','生徒名','メール','電話','金額','PaymentIntentId','エラーコード','詳細','registrationId']];
  const push = (status, r) => rows.push([
    data.month, status, r.studentName || '', r.email || '', r.phone || '',
    r.amount || 0, r.paymentIntentId || '',
    r.errorCode || '', (r.errorDetail || r.idempotencyKey || '').replace(/[\r\n]/g, ' '),
    r.registrationId || '',
  ]);
  (data.success || []).forEach(r => push('success', r));
  (data.failed || []).forEach(r => push('failed', r));
  (data.requires_action || []).forEach(r => push('requires_action', r));
  (data.uncertain || []).forEach(r => push('uncertain', r));
  const csv = rows.map(row => row.map(x => '"' + String(x || '').replace(/"/g, '""') + '"').join(',')).join('\n');
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = `juku-monthly-history-${data.month}.csv`;
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ===========================================================================
// 📖 引き落とし台帳 (月別 × 生徒・2026-07-02 塾長要望)
//   「誰の何月分をカードから引き落とし済みか」を一目で確認し、
//   請求対象月で未請求の人はマス内の「💳 個別請求」からそのまま請求できる。
//   データは read-only の /payment/api/admin-charge-ledger (charge:history 等の集計)。
// ===========================================================================

async function fetchChargeLedger() {
  const statusEl = document.getElementById('ledgerStatus');
  const pw = getMonthEndAdminPw();
  if (!statusEl) return;
  if (!pw) { statusEl.innerHTML = '<span style="color:#fbbf24">🔒 管理パスワードを入力すると台帳が表示されます</span>'; return; }
  // 名簿プレビュー未取得のまま台帳だけ描くと全員が「(現名簿外)」の薄字になってしまう。
  // 先にプレビューを取りに行く (成功時にこの関数が自動で呼ばれる・失敗時は連鎖しないのでループしない)。
  if (!MONTHEND_STATE.lastPreview) {
    statusEl.innerHTML = '<span style="color:var(--text-dim)">⏳ 先に名簿プレビューを取得しています...</span>';
    fetchMonthEndPreview();
    return;
  }
  if (MONTHEND_STATE.ledgerBusy) return;
  MONTHEND_STATE.ledgerBusy = true;
  statusEl.innerHTML = '<span style="color:var(--text-dim)">⏳ 台帳を取得中...</span>';
  try {
    const res = await fetch('/payment/api/admin-charge-ledger?months=6', {
      method: 'GET', headers: { 'X-Admin-Password': pw },
    });
    if (res.status === 401) { statusEl.innerHTML = '<span style="color:#f87171">❌ 認証失敗。管理パスワードを確認してください</span>'; return; }
    const data = await res.json();
    if (!res.ok) { statusEl.innerHTML = `<span style="color:#f87171">❌ ${escapeHtmlME(data.message || data.error || 'unknown')}</span>`; return; }
    MONTHEND_STATE.lastLedger = data;
    renderChargeLedger(data);
    const t = data.fetched_at ? new Date(data.fetched_at * 1000).toLocaleTimeString('ja-JP', { timeZone: 'Asia/Tokyo', hour: '2-digit', minute: '2-digit' }) : '';
    statusEl.innerHTML = t ? `<span style="color:var(--success);font-size:0.82rem;">✅ 台帳更新 (${t} 時点)</span>` : '';
  } catch (e) {
    statusEl.innerHTML = `<span style="color:#f87171">❌ ネットワークエラー: ${escapeHtmlME(e.message)}</span>`;
  } finally {
    MONTHEND_STATE.ledgerBusy = false;
  }
}

function renderChargeLedger(data) {
  const target = document.getElementById('ledgerResults');
  if (!target) return;
  const entries = Array.isArray(data.entries) ? data.entries : [];
  const preview = MONTHEND_STATE.lastPreview;
  const billMonth = (preview && preview.month) || '';
  const isSpotOk = s => (s === 'succeeded' || s === 'processing');

  // 表示する月列: サーバの months (翌月+今月+直近5ヶ月) を昇順 (左=古い→右=新しい)。
  // 翌月列はエントリがある (前倒し請求済み) か、いま翌月分モードで請求対象のときだけ出す。
  let months = (Array.isArray(data.months) ? data.months.slice() : []).sort();
  const nextM = data.next_month || '';
  if (nextM && months.indexOf(nextM) >= 0) {
    const hasNext = entries.some(e => e.month === nextM) || billMonth === nextM;
    if (!hasNext) months = months.filter(m => m !== nextM);
  }
  if (!months.length) { target.innerHTML = ''; return; }

  // rid → month → 月謝エントリ (優先度: 成功 > 3DS待ち > 要確認 > 失敗。失敗→再請求成功は成功を表示)
  const rankOf = s => ({ success: 3, requires_action: 2, uncertain: 1, failed: 0 })[s] !== undefined
    ? { success: 3, requires_action: 2, uncertain: 1, failed: 0 }[s] : -1;
  const cellMap = {};   // rid -> { month -> entry }
  const spotMap = {};   // rid -> { month -> [spot entries] }
  const nameByRid = {};
  for (const e of entries) {
    const rid = e.registrationId || '';
    if (!rid || !e.month) continue;
    if (e.studentName && !nameByRid[rid]) nameByRid[rid] = e.studentName;
    if (e.kind === 'spot') {
      // 同期失敗 (=塾長が請求モーダルで❌を目撃済みの確定未課金) はノイズなので出さない。
      // ★非同期失敗 (sourceEvent 有り = 3DS 拒否等を webhook が後から確定・誰も画面で見ていない)
      //   は❌で表示する。黙って消すと未回収の講習費が無音化するため (2026-07-02 review)
      if (e.status === 'failed' && !e.sourceEvent) continue;
      (spotMap[rid] = spotMap[rid] || {});
      (spotMap[rid][e.month] = spotMap[rid][e.month] || []).push(e);
    } else {
      const byMonth = (cellMap[rid] = cellMap[rid] || {});
      const cur = byMonth[e.month];
      if (!cur || rankOf(e.status) > rankOf(cur.status)) byMonth[e.month] = e;
    }
  }

  // 行 = 現在の名簿 (プレビューと同じ並び) + 履歴にだけ居る人 (退塾済みなど) を下に薄く
  const rosterRows = (preview && Array.isArray(preview.customers)) ? preview.customers : [];
  const rosterIds = new Set(rosterRows.map(c => c.registrationId));
  const seen = new Set();
  const historyOnly = [];
  for (const rid of Object.keys(cellMap).concat(Object.keys(spotMap))) {
    if (!rosterIds.has(rid) && !seen.has(rid)) { seen.add(rid); historyOnly.push(rid); }
  }
  if (!rosterRows.length && !historyOnly.length) {
    target.innerHTML = '<div style="color:var(--text-dim);padding:1rem;">まだ引き落とし履歴がありません</div>';
    return;
  }

  const monthTh = m => {
    const isBill = m === billMonth;
    return `<th class="ta-c" style="white-space:nowrap;${isBill ? 'background:rgba(99,102,241,0.15);border-bottom:2px solid var(--primary-light);' : ''}">${parseInt(m.slice(5), 10)}月<div style="font-size:0.68rem;font-weight:400;color:var(--text-dim)">${escapeHtmlME(m.slice(0, 4))}</div>${isBill ? '<div style="font-size:0.66rem;color:var(--primary-light);">今の請求対象</div>' : ''}</th>`;
  };

  // マス内の個別請求ボタンは「一斉実行後の追い請求」用: 請求対象月で誰かに請求済みのときだけ出す
  // (月初の全員未請求時に23個並んで「1人ずつ押す」誤運用を誘わないため。先行個別請求は上の名簿表から可能)
  const showCellButtons = !!(preview && preview.previously_charged_this_month > 0);
  const oneBtnHtml = (rid, m, retry) =>
    `<button class="btn btn-ghost btn-sm" onclick="chargeOneMonthEnd('${escapeHtmlME(rid)}', '${escapeHtmlME(m)}')" title="この人のこの月分だけ今すぐ${retry ? '再' : ''}請求 (他の人には請求されません)" style="color:#34d399;border-color:rgba(16,185,129,0.45);white-space:nowrap;">💳 個別請求</button>`;

  const cellHtml = (rid, m, rosterC) => {
    const e = (cellMap[rid] || {})[m];
    const chargeableHere = !!(rosterC && m === billMonth && rosterC.ready && !rosterC.alreadyChargedThisMonth && showCellButtons);
    let inner = '';
    if (e) {
      const d = fmtDateME(e.chargedAt);
      if (e.status === 'success') {
        inner = `<span style="color:var(--success);white-space:nowrap;">✅ ${fmtYenME(e.amount)}</span>${d ? `<div style="font-size:0.7rem;color:var(--text-dim)">${d}</div>` : ''}`;
      } else if (e.status === 'requires_action') {
        inner = `<span class="ledger-issue" data-month="${escapeHtmlME(m)}" style="color:#fbbf24;cursor:pointer;text-decoration:underline dotted;" title="クリックで下の詳細履歴を開く">🔐 3DS待ち</span>`;
      } else if (e.status === 'uncertain') {
        inner = `<span class="ledger-issue" data-month="${escapeHtmlME(m)}" style="color:#fbbf24;cursor:pointer;text-decoration:underline dotted;" title="クリックで下の詳細履歴を開く">⚠️ 要確認</span>`;
      } else {
        inner = `<span class="ledger-issue" data-month="${escapeHtmlME(m)}" style="color:#f87171;cursor:pointer;text-decoration:underline dotted;" title="クリックで下の詳細履歴を開く">❌ 失敗</span>`;
      }
      // ❌失敗はサーバ側でロック解除済み=再請求可能 (ready ∧ 未請求) なら個別請求ボタンを添える。
      // 🔐3DS待ち/⚠️要確認 は done ロック保持中 → alreadyChargedThisMonth=true なのでボタンは出ない (二重請求防止)。
      if (e.status === 'failed' && chargeableHere) {
        inner += `<div style="margin-top:3px;">${oneBtnHtml(rid, m, true)}</div>`;
      }
    } else if (chargeableHere) {
      // いまの請求対象月でまだ未請求 → その場で個別請求できるボタン (既存の chargeOneMonthEnd を使用)
      inner = oneBtnHtml(rid, m, false);
    } else {
      inner = '<span style="color:var(--text-dim)">―</span>';
    }
    const spots = (spotMap[rid] || {})[m] || [];
    for (const s of spots) {
      const ok = isSpotOk(s.status);
      const failed = s.status === 'failed';  // 非同期失敗のみここに来る (同期失敗は上でフィルタ済み)
      const color = ok ? '#a78bfa' : (failed ? '#f87171' : '#fbbf24');
      const suffix = ok ? '' : (failed ? ' ❌失敗' : ' ⚠️要確認');
      const titleNote = ok ? '' : (failed
        ? ' — 3DS/カード確認で失敗・未課金です (必要なら生徒一覧の🎓ボタンから再請求)'
        : ' — 課金されたか要確認 (Stripe ダッシュボードで確認してください)');
      inner += `<div style="font-size:0.72rem;color:${color};white-space:nowrap;" title="${escapeHtmlME(s.label || '講習費用')}${fmtDateME(s.chargedAt) ? ' ' + fmtDateME(s.chargedAt) : ''}${titleNote}">🎓 ${fmtYenME(s.amount)}${suffix}</div>`;
    }
    return `<td class="ta-c">${inner}</td>`;
  };

  let html = '<table class="table" style="min-width:720px;"><thead><tr><th style="min-width:120px;">生徒氏名</th>' + months.map(monthTh).join('') + '</tr></thead><tbody>';
  for (const c of rosterRows) {
    const rid = c.registrationId || '';
    html += `<tr><td style="white-space:nowrap;">${escapeHtmlME(c.studentName || nameByRid[rid] || rid)}</td>${months.map(m => cellHtml(rid, m, c)).join('')}</tr>`;
  }
  for (const rid of historyOnly) {
    html += `<tr style="opacity:0.55;"><td style="white-space:nowrap;">${escapeHtmlME(nameByRid[rid] || rid)} <span style="font-size:0.7rem;color:var(--text-dim)">(現名簿外)</span></td>${months.map(m => cellHtml(rid, m, null)).join('')}</tr>`;
  }

  // フッター: 月ごとの成功合計 (月謝) + 講習の成功合計
  html += '<tr style="border-top:2px solid rgba(255,255,255,0.15);font-weight:600;"><td>合計 (成功のみ)</td>';
  for (const m of months) {
    let sum = 0, cnt = 0, spotSum = 0;
    for (const e of entries) {
      if (e.month !== m) continue;
      if (e.kind === 'spot') { if (isSpotOk(e.status)) spotSum += Number(e.amount) || 0; }
      else if (e.status === 'success') { sum += Number(e.amount) || 0; cnt++; }
    }
    html += `<td class="ta-c" style="white-space:nowrap;">${cnt ? `${fmtYenME(sum)}<div style="font-size:0.68rem;color:var(--text-dim);font-weight:400;">${cnt}名</div>` : '<span style="color:var(--text-dim)">―</span>'}${spotSum ? `<div style="font-size:0.7rem;color:#a78bfa;font-weight:400;">🎓 ${fmtYenME(spotSum)}</div>` : ''}</td>`;
  }
  html += '</tr></tbody></table>';
  if (data.truncated) {
    html += '<div style="font-size:0.78rem;color:#fbbf24;margin-top:0.5rem;">⚠️ 件数が多いため一部のみ表示しています</div>';
  }
  html += '<div style="font-size:0.75rem;color:var(--text-dim);margin-top:0.5rem;">※ 成功履歴は1年間保存。それ以前の分は Stripe ダッシュボードでご確認ください。</div>';
  target.innerHTML = html;

  // ❌/⚠️/🔐 のマス → 下の詳細履歴パネルをその月で開く (再請求/reconcile ボタンがある)
  target.querySelectorAll('.ledger-issue').forEach(el => {
    el.addEventListener('click', () => {
      const m = el.dataset.month || '';
      const mi = document.getElementById('historyMonthInput');
      const tf = document.getElementById('historyTypeFilter');
      if (mi && m) mi.value = m;
      if (tf) tf.value = 'all';
      const det = mi ? mi.closest('details') : null;
      if (det) det.open = true;
      fetchChargeHistory();
      if (det && det.scrollIntoView) det.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });
}

// 🔧 uncertain reconcile モーダル
function openReconcileModal(rid, month, studentName, amount) {
  const modal = document.getElementById('reconcileModal');
  const body = document.getElementById('reconcileModalBody');
  body.innerHTML = `
    <div style="padding:1rem;background:rgba(245,158,11,0.08);border-radius:8px;margin-bottom:1rem;">
      <strong>${escapeHtmlME(studentName)}</strong> (月: ${escapeHtmlME(month)}・${fmtYenME(amount)})<br>
      <span style="font-size:0.85rem;color:var(--text-dim)">Stripe Dashboard で実際の状態を確認してから操作してください。</span>
    </div>
    <div style="display:flex;flex-direction:column;gap:0.75rem;">
      <button class="btn" onclick="reconcileCharge('${escapeHtmlME(rid)}', '${escapeHtmlME(month)}', 'mark_paid')" style="background:rgba(16,185,129,0.15);color:var(--success);border:1px solid var(--success);text-align:left;">
        ✅ <strong>実際は課金されていた</strong> → 成功として記録 (PI ID 任意入力)
      </button>
      <input type="text" id="reconcilePiId" placeholder="(任意) pi_xxx — PI ID を入れると Stripe で verify します" class="search-input" style="font-family:monospace;font-size:0.85rem">
      <button class="btn" onclick="reconcileCharge('${escapeHtmlME(rid)}', '${escapeHtmlME(month)}', 'mark_unpaid')" style="background:rgba(99,102,241,0.15);color:var(--primary-light);border:1px solid var(--primary-light);text-align:left;">
        ❌ <strong>実際は未課金だった</strong> → ロック解除 (この後 retry または手動で再請求)
      </button>
      <button class="btn" onclick="reconcileCharge('${escapeHtmlME(rid)}', '${escapeHtmlME(month)}', 'retry')" style="background:linear-gradient(135deg,#ef4444,#f59e0b);color:#fff;border:none;text-align:left;">
        🔁 <strong>未課金として即時再請求</strong> → 新しい PaymentIntent で再請求実行 (実際にカードに課金されます)
      </button>
    </div>
  `;
  modal.classList.remove('hidden');
  modal.style.display = 'flex';
}

async function reconcileCharge(rid, month, action) {
  // 🚨 3rd review fix: UI busy lock で連打防止
  if (MONTHEND_STATE.reconcileBusy === `${rid}:${month}`) {
    alert('既に処理中です。完了までお待ちください');
    return;
  }
  MONTHEND_STATE.reconcileBusy = `${rid}:${month}`;
  const pw = getMonthEndAdminPw();
  if (!pw) { alert('管理パスワードを入力してください'); MONTHEND_STATE.reconcileBusy = null; return; }
  let body = { action, registrationId: rid, month };
  if (action === 'mark_paid') {
    const piEl = document.getElementById('reconcilePiId');
    if (piEl) body.paymentIntentId = piEl.value.trim();
  }
  // 🚨 Round 4 fix: confirm キャンセル時に lock を必ず null に戻す (永久 lock 残留 bug 防止)
  if (action === 'retry') {
    if (!confirm(`🚨 ${rid} の月 ${month} を即時再請求します (実際にカードに課金されます)。\n\n本当に実行しますか?`)) {
      MONTHEND_STATE.reconcileBusy = null; return;
    }
  } else if (action === 'mark_paid') {
    if (!confirm(`${rid} を「成功」として確定します。本当によろしいですか? (Stripe Dashboard で確認済みであることを前提)`)) {
      MONTHEND_STATE.reconcileBusy = null; return;
    }
  } else if (action === 'mark_unpaid') {
    if (!confirm(`${rid} のロックを解除します。これで月末バッチで再度引き落とし対象になります。\n\n※ 🔐3DS待ちの分は残っていた PaymentIntent を自動でキャンセルします。\n※ ⚠️要確認の分で Stripe Dashboard に未完了の PaymentIntent を見つけた場合は、Dashboard 側でキャンセルしてから解除してください (放置すると後から二重課金になり得ます)。`)) {
      MONTHEND_STATE.reconcileBusy = null; return;
    }
  }
  try {
    const res = await fetch('/payment/api/admin-charge-reconcile', {
      method: 'POST',
      headers: { 'X-Admin-Password': pw, 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok || data.error) { alert(`❌ ${data.message || data.error || 'エラー'}`); return; }
    // ⚠️ warning = 「生きた 3DS PI を cancel できなかった/二重回収の可能性」等。黙殺すると
    // 二重課金の入口が silent に残るため必ず表示する (2026-07-02 round2 review)
    alert(data.warning ? `✅ ${action} 完了\n\n⚠️ ${data.warning}` : `✅ ${action} 完了`);
    document.getElementById('reconcileModal').style.display = 'none';
    // 履歴を再取得 + プレビュー/📖台帳も更新 (⚠️マスや個別請求ボタンを stale にしない)
    fetchChargeHistory();
    setTimeout(() => fetchMonthEndPreview(), 500);
  } catch (e) {
    alert(`❌ ${e.message}`);
  } finally {
    MONTHEND_STATE.reconcileBusy = null;
  }
}

// 🔁 個別再請求 (failed 状態から)
async function retryCharge(rid, month, studentName, amount) {
  // 🚨 3rd review fix: UI busy lock で連打防止 (server 側 lock 429 と二重防御)
  if (MONTHEND_STATE.retryBusy === `${rid}:${month}`) {
    alert('既に再請求処理中です。完了までお待ちください');
    return;
  }
  MONTHEND_STATE.retryBusy = `${rid}:${month}`;
  // 🚨 Round 4 fix: 既に lock cleanup OK (retryBusy = null on all returns)
  const pw = getMonthEndAdminPw();
  if (!pw) { alert('管理パスワードを入力してください'); MONTHEND_STATE.retryBusy = null; return; }
  if (!confirm(`🚨 ${studentName} (${fmtYenME(amount)}) を即時再請求します (実際にカードに課金されます)。\n\n本当に実行しますか?`)) { MONTHEND_STATE.retryBusy = null; return; }
  // failed → 先に mark_unpaid で lock 解除 (= done_key 削除) してから retry
  try {
    // 1. mark_unpaid
    const r1 = await fetch('/payment/api/admin-charge-reconcile', {
      method: 'POST', headers: { 'X-Admin-Password': pw, 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'mark_unpaid', registrationId: rid, month }),
    });
    const d1 = await r1.json();
    if (!r1.ok || d1.error) { alert(`❌ unlock 失敗: ${d1.message || d1.error}`); return; }
    if (d1.warning) alert(`⚠️ ${d1.warning}`);
    // 2. retry
    const r2 = await fetch('/payment/api/admin-charge-reconcile', {
      method: 'POST', headers: { 'X-Admin-Password': pw, 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'retry', registrationId: rid, month }),
    });
    const d2 = await r2.json();
    if (!r2.ok || d2.error) { alert(`❌ retry 失敗: ${d2.message || d2.error}\n${d2.detail || ''}`); return; }
    alert(`✅ retry 完了: ${d2.paymentIntentId || ''} (${d2.stripeStatus || ''})`);
    fetchChargeHistory();
    setTimeout(() => fetchMonthEndPreview(), 500);   // ❌マス/バナーを stale にしない (📖台帳も連鎖更新)
  } catch (e) {
    alert(`❌ ${e.message}`);
  } finally {
    MONTHEND_STATE.retryBusy = null;
  }
}

// 🗑 退塾処理 (preview の各行からも呼ばれる想定)
async function cancelRegistration(rid, studentName) {
  // 🚨 3rd review fix: UI busy lock で連打防止
  if (MONTHEND_STATE.cancelBusy === rid) {
    alert('既に退塾処理中です。完了までお待ちください');
    return;
  }
  MONTHEND_STATE.cancelBusy = rid;
  const pw = getMonthEndAdminPw();
  if (!pw) { alert('管理パスワードを入力してください'); MONTHEND_STATE.cancelBusy = null; return; }
  // 🚨 2nd review fix: studentName が空文字の case を弾く
  if (!studentName || !studentName.trim()) { alert('生徒氏名が空です。データ破損の可能性があるため中止します。'); MONTHEND_STATE.cancelBusy = null; return; }
  if (!confirm(`🗑 ${studentName} の登録を解除します。\n\nこの操作で:\n- カード情報が Stripe から detach されます\n- 以降の月末バッチに表示されません\n- 過去の引き落とし履歴は残ります (1 年)\n\n続行しますか?`)) { MONTHEND_STATE.cancelBusy = null; return; }
  const typed = prompt(`安全のため生徒氏名を正確に入力してください: ${studentName}`);
  if (typed === null) { MONTHEND_STATE.cancelBusy = null; return; }
  // 🚨 2nd review fix: 空文字 typed や trim 後一致を厳密に
  if (!typed || typed.trim() !== studentName.trim()) {
    alert(`氏名 (${typed}) が一致しません (期待: ${studentName})。中止します。`);
    MONTHEND_STATE.cancelBusy = null; return;
  }
  const reason = prompt('退塾理由 (任意・空欄可):', '退塾');
  try {
    const res = await fetch('/payment/api/admin-registration-cancel', {
      method: 'POST', headers: { 'X-Admin-Password': pw, 'Content-Type': 'application/json' },
      body: JSON.stringify({ registrationId: rid, reason: reason || '退塾', confirmStudentName: studentName }),
    });
    const data = await res.json();
    // 🚨 2nd review fix: 502 (Stripe detach 失敗) の case を明示的に handle
    if (res.status === 502) {
      const errs = (data.stripe_errors || []).join('\n');
      alert(`⚠️ Stripe detach 失敗のため退塾処理を中断しました。KV は変更されていません。\n\nエラー:\n${errs}\n\nStripe Dashboard で状態を確認後、再度お試しください。`);
      return;
    }
    if (!res.ok || data.error) { alert(`❌ ${data.message || data.error}`); return; }
    alert(`✅ ${data.message || '退塾処理完了'}`);
    fetchMonthEndPreview();
  } catch (e) {
    alert(`❌ ${e.message}`);
  } finally {
    MONTHEND_STATE.cancelBusy = null;
  }
}

function downloadMonthEndResultCsv() {
  const data = MONTHEND_STATE.lastResult;
  if (!data || !data.results) return;
  const rows = [['月','生徒名','メール','電話','金額','状態','Stripe状態','PaymentIntentId','エラーコード','拒否コード','詳細','registrationId']];
  for (const r of data.results) {
    rows.push([
      data.month, r.studentName || '', r.email || '', r.phone || '',
      r.amount || 0, r.status || '', r.stripeStatus || '', r.paymentIntentId || '',
      r.errorCode || '', r.declineCode || '',
      (r.error || r.reason || '').replace(/[\r\n]/g, ' '),
      r.registrationId || '',
    ]);
  }
  const csv = rows.map(row => row.map(x => '"' + String(x || '').replace(/"/g, '""') + '"').join(',')).join('\n');
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `juku-monthly-result-${data.month}-${data.dry_run ? 'dryrun' : 'live'}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function downloadMonthEndCsv() {
  const data = MONTHEND_STATE.lastPreview;
  if (!data || !data.customers) return;
  const rows = [['月','生徒氏名','学年','保護者氏名','メール','電話','月額','内訳','状態','registrationId','customerId']];
  for (const c of data.customers) {
    rows.push([
      data.month, c.studentName, c.grade, c.parentName, c.email, c.phone || '',
      c.monthlyFee, c.feeBreakdown, c.ready ? 'ready' : (c.issue || ''),
      c.registrationId, c.customerId,
    ]);
  }
  const csv = rows.map(r => r.map(x => '"' + String(x || '').replace(/"/g, '""') + '"').join(',')).join('\n');
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `juku-monthly-preview-${data.month}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
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

// 異体字 / 旧字体 → 常用字体 (姓名で同一人物を表す字体ゆれを吸収・2026-06-02)
// 例: 名簿「野澤」⇄カード登録「野沢」、「髙田」⇄「高田」が別人扱いされて重複登録される事故の防止。
// 同じ名前を表す字体ペアのみ収録 (別の名前を誤って同一視しないよう保守的に維持)。
const KANJI_VARIANTS = {
  '澤':'沢','髙':'高','﨑':'崎','嵜':'崎','邊':'辺','邉':'辺','齋':'斎','齊':'斉',
  '廣':'広','濵':'浜','濱':'浜','國':'国','圀':'国','萬':'万','惠':'恵','桒':'桑',
  '眞':'真','靜':'静','晉':'晋','應':'応','戶':'戸','黑':'黒','條':'条','圓':'円',
  '樂':'楽','數':'数','藥':'薬','寬':'寛','冨':'富','嶋':'島','嶌':'島','槇':'槙',
  '龍':'竜','假':'仮','兒':'児','莊':'荘','顯':'顕','賴':'頼','禮':'礼','來':'来',
  '學':'学','櫻':'桜','龜':'亀','濟':'済','鄕':'郷','縣':'県','澁':'渋','瀧':'滝',
  '瀨':'瀬','增':'増','德':'徳','凉':'涼','渕':'淵','渊':'淵','萊':'莱','緖':'緒',
  '𠮷':'吉',
};
const KANJI_VARIANT_RE = new RegExp(Object.keys(KANJI_VARIANTS).join('|'), 'gu');

const IMPORT = { rows: [], candidates: [], filterTab: 'pending' };

function normalizeName(raw) {
  if (!raw) return '';
  let s = String(raw);
  s = s.replace(/[ｦ-ﾝ]/g, c => HW_KANA_MAP[c] || c);
  s = s.replace(/(.)[゛ﾞ]/g, (m, c) => DAKUTEN[c] || c);
  s = s.replace(/(.)[゜ﾟ]/g, (m, c) => HANDAKUTEN[c] || c);
  s = s.replace(/[ァ-ヶ]/g, m => String.fromCharCode(m.charCodeAt(0) - 0x60));
  s = s.replace(/づ/g, 'ず').replace(/ぢ/g, 'じ');
  s = s.replace(KANJI_VARIANT_RE, c => KANJI_VARIANTS[c] || c);  // 異体字/旧字体を常用字体に寄せる
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
      <div style="font-weight:600; color:#374151; margin-bottom:4px;">${escapeHtml(SETTINGS.jukuName || 'AIコーチング')}</div>
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
        // 2026-06-03: バックアップ復元で 編集/追加生徒/紐付け/招待送信記録 を失わない (ov 優先で現行に重ねる)
        stripeInviteSent: { ...(STATE.overrides.stripeInviteSent || {}), ...(ov.stripeInviteSent || {}) },
        regLinks: { ...(STATE.overrides.regLinks || {}), ...(ov.regLinks || {}) },
        studentEdits: { ...(STATE.overrides.studentEdits || {}), ...(ov.studentEdits || {}) },
        newStudents: (() => {
          const cur = Array.isArray(STATE.overrides.newStudents) ? STATE.overrides.newStudents.slice() : [];
          const ids = new Set(cur.map(s => s && s.id));
          for (const ns of (Array.isArray(ov.newStudents) ? ov.newStudents : [])) {
            if (ns && typeof ns.id === 'number' && !ids.has(ns.id)) { cur.push(ns); ids.add(ns.id); }
          }
          return cur;
        })(),
        // 2026-06-30: 申込取込済み id も失わない (= 取込済み申込がバックアップ復元で再出現するのを防ぐ)
        importedAppIds: Array.from(new Set([
          ...(Array.isArray(STATE.overrides.importedAppIds) ? STATE.overrides.importedAppIds : []),
          ...(Array.isArray(ov.importedAppIds) ? ov.importedAppIds : []),
        ])),
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
    // 2026-06-03: 復元した 追加生徒/編集 を in-memory に反映 (元データ差し替え後に再適用)
    if (typeof mergeNewStudentsIntoData === 'function') mergeNewStudentsIntoData();
    if (typeof applyStudentEdits === 'function') applyStudentEdits();
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
      // 管理パスワード変更時は Stripe 登録キャッシュを無効化 → 全生徒タブのカード列が
      // 新 pw で再取得される (旧 pw 時の「全員未登録」表示が残るのを防ぐ)。
      STRIPE_CUST_CACHE.customers = [];
      STRIPE_CUST_CACHE.loadedAt = 0;
      STRIPE_CUST_CACHE._allTabTried = false;
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

  // 2026-06-30 追加: 入塾申込フォーム取り込み
  const iab = document.getElementById('importAppsBtn');
  if (iab) iab.addEventListener('click', openImportAppsModal);
  const iacb = document.getElementById('importAppsCloseBtn');
  if (iacb) iacb.addEventListener('click', closeImportAppsModalSafe);
  const iarb = document.getElementById('importAppsRefreshBtn');
  if (iarb) iarb.addEventListener('click', renderImportAppsList);
  // 起動後にバッジ件数を静かに更新 (token があれば)
  setTimeout(() => { try { refreshImportAppsBadge(); } catch (e) {} }, 2500);

  // 2026-06-03: 生徒編集モーダル
  const escb = document.getElementById('editStudentCancelBtn');
  if (escb) escb.addEventListener('click', closeEditStudentModalSafe);
  const essb = document.getElementById('editStudentSaveBtn');
  if (essb) essb.addEventListener('click', saveStudentEdit);
  const esrb = document.getElementById('editStudentResetBtn');
  if (esrb) esrb.addEventListener('click', resetStudentEdit);
  const escc = document.getElementById('editStudentClearCourses');
  if (escc) escc.addEventListener('click', async () => {
    const ta = document.getElementById('editStudentCourses');
    if (ta) { ta.value = ''; syncEditChipActive(); await autoAdjustFeeForCourseChange(); }
  });
  const esrf = document.getElementById('editStudentRecalcFee');
  if (esrf) esrf.addEventListener('click', recalcEditFeeFromCourses);

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

  // 💳 月末一斉引き落とし (2026-05-13 塾長指示)
  document.getElementById('monthEndRefreshBtn')?.addEventListener('click', fetchMonthEndPreview);
  document.getElementById('monthEndDryRunBtn')?.addEventListener('click', () => executeMonthEndCharge(true));
  document.getElementById('monthEndExecuteBtn')?.addEventListener('click', () => executeMonthEndCharge(false));
  // 🕒 滞納分も含める トグル (2026-06-01): ON で過去3ヶ月の未払い月もカード一括対象に
  document.getElementById('monthEndIncludeArrears')?.addEventListener('change', (e) => {
    MONTHEND_STATE.includeArrears = !!e.target.checked;
    if (MONTHEND_STATE.lastPreview) renderMonthEndTable(MONTHEND_STATE.lastPreview);
  });
  // 📅 請求対象月セレクタ (2026-06-26): 今月分 / 翌月分。切替で再プレビュー。
  // 翌月分モードでは滞納分トグルを無効化 (誤請求防止)。
  document.querySelectorAll('input[name="monthEndBillMode"]').forEach((el) => {
    el.addEventListener('change', (e) => {
      MONTHEND_STATE.billMode = e.target.value === 'next' ? 'next' : 'current';
      const arr = document.getElementById('monthEndIncludeArrears');
      if (arr) {
        if (MONTHEND_STATE.billMode === 'next') {
          arr.checked = false;
          arr.disabled = true;
          MONTHEND_STATE.includeArrears = false;
        } else {
          arr.disabled = false;
        }
      }
      MONTHEND_STATE.excluded = new Set();   // モード切替で選択状態はリセット
      if (getMonthEndAdminPw()) fetchMonthEndPreview();
      else if (MONTHEND_STATE.lastPreview) renderMonthEndTable(MONTHEND_STATE.lastPreview);
    });
  });
  document.getElementById('monthEndExportCsvBtn')?.addEventListener('click', downloadMonthEndCsv);
  document.getElementById('monthEndAdminPw')?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') fetchMonthEndPreview();
  });
  document.getElementById('monthEndResultClose')?.addEventListener('click', () => {
    const modal = document.getElementById('monthEndResultModal');
    if (modal) { modal.classList.add('hidden'); modal.style.display = 'none'; }
  });

  // 📜 履歴 / 🔧 reconcile / 🗑 退塾 (2nd review 反映)
  document.getElementById('historyFetchBtn')?.addEventListener('click', fetchChargeHistory);
  document.getElementById('historyCsvBtn')?.addEventListener('click', downloadHistoryCsv);
  // 📖 引き落とし台帳 (月別 × 生徒)
  document.getElementById('ledgerRefreshBtn')?.addEventListener('click', fetchChargeLedger);
  document.getElementById('reconcileModalClose')?.addEventListener('click', () => {
    const modal = document.getElementById('reconcileModal');
    if (modal) { modal.classList.add('hidden'); modal.style.display = 'none'; }
  });
  // 📌 inline onclick で呼ぶ関数を global にエクスポート (memory: feedback_iife_onclick_pitfall.md)
  window.cancelRegistration = cancelRegistration;
  window.openReconcileModal = openReconcileModal;
  window.reconcileCharge = reconcileCharge;
  window.retryCharge = retryCharge;
}

async function init() {
  STATE.currentMonth = todayMonth();
  document.getElementById('monthInput').value = STATE.currentMonth;

  loadSettings();
  await loadData();
  await loadCourseMap();         // コースID→名前マップを確定 (正規化に必須なので await)
  normalizeStudentCourses();     // long-1 等のID を 英語長文レベル１ 等の正式名に統合
  // 2026-05-07: クラウド sync 初期化 (token があれば pull → local 上書き)
  updateSyncStatusBar();
  await CloudSync.bootstrap();
  normalizeStudentCourses();     // pull で取り込んだ生徒も正規化
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
