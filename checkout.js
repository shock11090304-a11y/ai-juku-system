// Checkout page: Stripe integration
const API_BASE = window.location.origin.includes(':8090')
  ? 'http://localhost:8000'  // dev: FastAPI on :8000, frontend on :8090
  : window.location.origin;  // prod: same origin

const PLAN_INFO = {
  founder_special:  { name: '🎁 創設メンバープラン (永年¥14,500)', price: 14500 },
  standard:  { name: 'スタンダード',     price: 24980 },
  premium:   { name: 'プレミアム',       price: 39800 },
  family:    { name: '家族プラン（最大3名）', price: 59800 },
  student_addon: { name: '🎓 通塾生プラン (永年¥5,000)', price: 5000 },
  // 旧プラン（後方互換用）
  ai:        { name: 'スタンダード',     price: 24980 },
  hybrid:    { name: 'プレミアム',       price: 39800 },
  intensive: { name: '家族プラン（最大3名）', price: 59800 },
};

function yen(n) { return '¥' + n.toLocaleString(); }

function updateSummary() {
  const plan = document.querySelector('input[name="plan"]:checked').value;
  const info = PLAN_INFO[plan];
  document.getElementById('summaryPlan').textContent = info.name;
  document.getElementById('summaryPrice').textContent = yen(info.price) + '（税込）';
  // 入塾金 ¥10,000 は student_addon 以外のプランに適用。選択プランによって表示を切替。
  const enrollmentRow = document.getElementById('summaryEnrollmentRow');
  if (enrollmentRow) {
    enrollmentRow.style.display = (plan === 'student_addon') ? 'none' : '';
  }
  // 🚨 2026-05-07: submit ボタン文言を plan で動的に変える (致命修正)
  // student_addon は本契約 (即課金) なので「無料体験」文言は誤誘導
  // 🎁 2026-05-19: +7 日延長 opt-in を反映 (14日 ↔ 21日 動的切替)
  const submitBtn = document.getElementById('submitBtn');
  if (submitBtn && !submitBtn.disabled) {
    if (plan === 'student_addon') {
      submitBtn.textContent = '💳 ¥5,000/月で登録する →';
    } else {
      const ext = !!document.getElementById('enableCardExtension')?.checked;
      submitBtn.textContent = ext
        ? '🎁 14日間 完全無料体験を開始する (クレカ登録) →'
        : '🎁 7日間 無料体験を開始する →';
    }
  }
  // 体験期間説明セクションも plan に応じて切替
  const trialNote = document.getElementById('trialNote');
  if (trialNote) {
    trialNote.style.display = (plan === 'student_addon') ? 'none' : '';
  }
  const studentAddonNote = document.getElementById('studentAddonNote');
  if (studentAddonNote) {
    studentAddonNote.style.display = (plan === 'student_addon') ? '' : 'none';
  }
  // 🚀 2026-05-29: 即時本契約 第2 CTA は student_addon (元々即課金) では不要 → 非表示
  const immBlock = document.getElementById('immediateBlock');
  if (immBlock) {
    immBlock.style.display = (plan === 'student_addon') ? 'none' : '';
  }
}

// Pre-fill from URL params (from LP link)
const params = new URLSearchParams(window.location.search);
if (params.get('plan') && PLAN_INFO[params.get('plan')]) {
  // ⚠️ checkout.html には standard/premium/family の 3 ラジオしか無いので、
  // founder_special など radio が無いプラン名で来ると querySelector が null を返す。
  // 旧コードは null.checked = true で TypeError 発生 → 以下の updateSummary と form
  // submit listener の登録が走らずフォームが完全に沈黙していた致命バグ (2026-04-27 修正)。
  const target = document.querySelector(`input[value="${params.get('plan')}"]`);
  if (target) {
    target.checked = true;
  }
  // founder_special / student_addon など対応 radio 無しの URL plan は submit 時に上書き利用。
  // 2026-05-07: student_addon は radio が UI に追加されたため、URL plan=student_addon は radio.check + summary 更新
  const overridablePlans = ['founder_special'];
  if (!target && overridablePlans.includes(params.get('plan'))) {
    window.__urlPlanOverride = params.get('plan');
  }
  if (params.get('plan') === 'student_addon' && target) {
    target.checked = true;
    target.dispatchEvent(new Event('change', { bubbles: true }));
    const summary = document.getElementById('summaryPlan');
    if (summary) summary.textContent = '通塾生プラン (永年¥5,000)';
    const summaryPrice = document.getElementById('summaryPrice');
    if (summaryPrice) summaryPrice.textContent = '¥5,000/月(税込)';
    const enrollmentRow = document.getElementById('summaryEnrollmentRow');
    if (enrollmentRow) enrollmentRow.style.display = 'none';
  }
}

// 招待トークン (student-upgrade.html 経由 or URL ?invite= で渡される) を保持
// 2026-05-07: 入力欄 #inviteCode に URL 値を auto-fill (塾長指示 = 申し込み画面に招待コード入力欄)
// 2026-05-07 update: ?invite_code=AJK-XXX の短いコード方式も受け付ける (URL token typo 事故対策)
window.__inviteToken = params.get('invite') || params.get('invite_code') || '';
if (window.__inviteToken) {
  const inviteEl = document.getElementById('inviteCode');
  if (inviteEl) inviteEl.value = window.__inviteToken;
}
if (params.get('email')) document.getElementById('email').value = params.get('email');
if (params.get('lastName')) document.getElementById('lastName').value = params.get('lastName');
if (params.get('firstName')) document.getElementById('firstName').value = params.get('firstName');
if (params.get('grade')) document.getElementById('grade').value = params.get('grade');
if (params.get('goal')) document.getElementById('goal').value = params.get('goal');

updateSummary();
document.querySelectorAll('input[name="plan"]').forEach(r => r.addEventListener('change', updateSummary));

// 🚀 2026-05-29 塾長指示: 体験スキップ即時本契約 第2 CTA。
//   クリックで __skipTrialImmediate を立て、共通の submit ハンドラ (バリデーション込み) を再利用。
//   submit ハンドラ側で endpoint が /api/stripe/checkout (即課金) に切り替わる。
(function () {
  const immBtn = document.getElementById('immediateBtn');
  const form = document.getElementById('checkoutForm');
  if (immBtn && form) {
    immBtn.addEventListener('click', function (e) {
      e.preventDefault();
      if (immBtn.disabled) return;
      window.__skipTrialImmediate = true;
      immBtn.disabled = true;
      immBtn.textContent = '📮 送信中... (1〜2秒)';
      // 即時送信 in-flight 中は体験ボタンも無効化 (二重 submit ハンドラ起動防止・UX クリーン化)
      const _sb = document.getElementById('submitBtn');
      if (_sb) _sb.disabled = true;
      // requestSubmit で submit イベントを発火 (バリデーション + 既存ロジックを共用)
      if (typeof form.requestSubmit === 'function') {
        form.requestSubmit();
      } else {
        form.dispatchEvent(new Event('submit', { cancelable: true }));
      }
    });
  }
})();

// キャリアメール (ezweb / docomo / au / softbank) を判定。
// 受信許可設定が無いと magic link 招待メールがブロックされやすい現実があるため、
// checkout 時に明示注意 + checkout-success / auth で対処手順を強調する。
const CARRIER_EMAIL_REGEX = /@(docomo\.ne\.jp|ezweb\.ne\.jp|au\.com|softbank\.ne\.jp|i\.softbank\.jp|ymobile\.ne\.jp|vodafone\.ne\.jp|ido\.ne\.jp|d\.vodafone\.ne\.jp|ezweb\.ne|disney\.ne\.jp|emnet\.ne\.jp|willcom\.com|wcm\.ne\.jp|jp-d\.ne\.jp|jp-h\.ne\.jp|jp-k\.ne\.jp|jp-n\.ne\.jp|jp-r\.ne\.jp|jp-s\.ne\.jp|jp-t\.ne\.jp|pdx\.ne\.jp|wm\.pdx\.ne\.jp|di\.pdx\.ne\.jp|dj\.pdx\.ne\.jp|dk\.pdx\.ne\.jp|t\.vodafone\.ne\.jp|h\.vodafone\.ne\.jp|q\.vodafone\.ne\.jp|n\.vodafone\.ne\.jp|c\.vodafone\.ne\.jp|k\.vodafone\.ne\.jp|r\.vodafone\.ne\.jp|s\.vodafone\.ne\.jp)$/i;
function isCarrierEmail(e) {
  return CARRIER_EMAIL_REGEX.test((e || '').trim().toLowerCase());
}
function isValidEmailFormat(e) {
  // HTML5 互換の最小バリデーション (空白なし + @ + . を満たす)
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test((e || '').trim());
}

// 入力時にキャリアメール注意を inline 表示
(function setupEmailHint() {
  const emailEl = document.getElementById('email');
  if (!emailEl) return;
  const hint = document.createElement('p');
  hint.id = 'emailCarrierHint';
  hint.style.cssText = 'display:none;margin-top:0.45rem;padding:0.65rem 0.8rem;background:rgba(251,191,36,0.10);border:1px solid rgba(251,191,36,0.35);border-radius:8px;color:#fbbf24;font-size:0.82rem;line-height:1.55;';
  hint.innerHTML = '⚠️ <strong>キャリアメール検出</strong>: docomo / ezweb / au / softbank はログインメールがブロックされやすい設定です。<strong>可能であれば Gmail / iCloud / Yahoo メール</strong> を推奨します。<br>キャリアメールのまま進める場合は、後ほどご案内する「PCからのメール受信許可」設定を必ず行ってください。';
  emailEl.parentNode.appendChild(hint);
  emailEl.addEventListener('input', () => {
    hint.style.display = isCarrierEmail(emailEl.value) ? 'block' : 'none';
  });
})();

document.getElementById('checkoutForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const submitBtn = document.getElementById('submitBtn');
  const errorBox = document.getElementById('errorBox');
  const loadingBox = document.getElementById('loadingBox');

  // 🚀 2026-05-29: 即時本契約フラグを one-shot で消費 (この submit だけに適用・次回 submit に漏らさない)
  const _immediateSubmit = (window.__skipTrialImmediate === true);
  window.__skipTrialImmediate = false;

  // URL ?plan=founder_special で来た場合は radio に対応無しのため override を優先
  const plan = window.__urlPlanOverride || document.querySelector('input[name="plan"]:checked').value;
  const lastName = (document.getElementById('lastName').value || '').trim();
  const firstName = (document.getElementById('firstName').value || '').trim();
  const email = (document.getElementById('email').value || '').trim();
  const studentEmailEl = document.getElementById('studentEmail');
  const studentEmail = studentEmailEl ? (studentEmailEl.value || '').trim() : '';
  const grade = document.getElementById('grade').value;
  if (!lastName || !firstName) {
    errorBox.textContent = '⚠️ フルネーム（姓と名の両方）を入力してください。';
    errorBox.style.display = 'block';
    submitBtn.disabled = false;
    { const _ib = document.getElementById('immediateBtn'); if (_ib) { _ib.disabled = false; _ib.textContent = '⚡ 体験をスキップして今すぐ本契約で始める →'; } }
    return;
  }
  if (!isValidEmailFormat(email)) {
    errorBox.textContent = '⚠️ メールアドレスの形式が正しくありません。 (例: parent@example.com)';
    errorBox.style.display = 'block';
    submitBtn.disabled = false;
    { const _ib = document.getElementById('immediateBtn'); if (_ib) { _ib.disabled = false; _ib.textContent = '⚡ 体験をスキップして今すぐ本契約で始める →'; } }
    return;
  }
  // 生徒メールは任意。入力されていれば形式チェック
  if (studentEmail && !isValidEmailFormat(studentEmail)) {
    errorBox.textContent = '⚠️ 生徒様メールアドレスの形式が正しくありません。空欄でも構いません。';
    errorBox.style.display = 'block';
    submitBtn.disabled = false;
    { const _ib = document.getElementById('immediateBtn'); if (_ib) { _ib.disabled = false; _ib.textContent = '⚡ 体験をスキップして今すぐ本契約で始める →'; } }
    return;
  }
  if (!grade) {
    errorBox.textContent = '⚠️ 学年を選択してください。';
    errorBox.style.display = 'block';
    submitBtn.disabled = false;
    { const _ib = document.getElementById('immediateBtn'); if (_ib) { _ib.disabled = false; _ib.textContent = '⚡ 体験をスキップして今すぐ本契約で始める →'; } }
    return;
  }
  // 紹介コード: URL ?ref= or localStorage に保存されていれば payload に乗せる (30日 TTL)
  let refCode = '';
  try {
    const urlRef = new URLSearchParams(window.location.search).get('ref');
    if (urlRef) refCode = urlRef.trim();
    if (!refCode) {
      const stored = localStorage.getItem('ai_juku_ref');
      if (stored) {
        const obj = JSON.parse(stored);
        // 30日以内なら有効
        if (obj && obj.code && obj.ts && (Date.now() - obj.ts) < 30 * 86400 * 1000) {
          refCode = obj.code;
        }
      }
    }
  } catch (e) { /* noop */ }

  // 📊 集客 attribution (塾長指示 2026-05-19): URL params + sessionStorage から utm 収集
  // フロントが追跡してきた流入元を signup と一緒に backend に送る → students テーブルに保存 → paid 化分析の基盤データ
  function _collectAttribution() {
    const attr = { utm_source: null, utm_content: null, utm_campaign: null, lp_variant: null, referrer: null };
    try {
      const sp = new URLSearchParams(window.location.search);
      attr.utm_source = sp.get('utm_source') || null;
      attr.utm_content = sp.get('utm_content') || null;
      attr.utm_campaign = sp.get('utm_campaign') || null;
      // lp_variant は lp.html (bandit) が localStorage.aj_lp_variant に書き込む
      attr.lp_variant = localStorage.getItem('aj_lp_variant') || null;
      // referrer (utm 無し時の補助)
      attr.referrer = document.referrer ? document.referrer.slice(0, 500) : null;
    } catch (_) { /* graceful */ }
    return attr;
  }
  const attribution = _collectAttribution();

  const payload = {
    plan,
    name: `${lastName}${firstName}`,
    email,
    student_email: studentEmail,  // 任意 (空欄なら保護者メールのみ)
    grade,
    goal: document.getElementById('goal').value,
    ref: refCode || undefined,
    ...attribution,  // utm_source / utm_content / utm_campaign / lp_variant / referrer
  };

  submitBtn.disabled = true;
  submitBtn.textContent = '📮 送信中... (1〜2秒)';
  errorBox.style.display = 'none';
  loadingBox.style.display = 'block';

  // 🛡️ 2026-05-21 P0-3: cache-purge.js が submit 中に location.reload() を
  // 発火する race を防ぐためのフラグ。完了時 (try/catch/finally) で false に戻す。
  window.__checkout_in_flight = true;

  // 🛡️ 2026-05-21 P0-2: fetch timeout wrapper (iPhone Safari 背景タブ stall 対策)
  // 20 秒で abort して loadingBox を強制 hide。
  async function fetchWithTimeout(url, opts, timeoutMs = 20000) {
    const ctrl = new AbortController();
    const tm = setTimeout(() => ctrl.abort(), timeoutMs);
    try {
      return await fetch(url, { ...opts, signal: ctrl.signal });
    } finally {
      clearTimeout(tm);
    }
  }

  // 🛡️ 2026-05-21 P0-1: response.json() を読んで具体エラー文言を user に表示
  // (429 / 422 / 400 を全て BACKEND_DOWN に丸めていた silent 機会損失 fix)
  async function readErrorDetail(res, defaultMsg) {
    try {
      const data = await res.json();
      if (data && typeof data.detail === 'string' && data.detail) return data.detail;
      if (data && typeof data.message === 'string' && data.message) return data.message;
    } catch (_e) { /* JSON ない場合 */ }
    return defaultMsg;
  }

  // 🛡️ 2026-05-21 XSS 防御: backend detail を errorBox.innerHTML に表示する前に escape
  // HTTPException(detail=...) が user 入力を echo する可能性があるため必須 (Agent review)
  function _esc(s) {
    const d = document.createElement('div');
    d.textContent = String(s == null ? '' : s);
    return d.innerHTML;
  }

  try {
    // 1. Register trial (creates student record)
    const signupRes = await fetchWithTimeout(`${API_BASE}/api/trial/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }, 20000);

    if (!signupRes.ok) {
      // 🛡️ P0-1: status 別に具体エラー表示 (silent 化 解消)
      if (signupRes.status === 429) {
        const detail = await readErrorDetail(signupRes,
          'ただ今混み合っています。5 分ほど待ってから再度お試しください。');
        throw new Error('RATE_LIMITED: ' + detail);
      }
      if (signupRes.status === 422 || signupRes.status === 400) {
        const detail = await readErrorDetail(signupRes,
          '入力内容に不備があります。フルネーム + Gmail 等のメールアドレスをご確認ください。');
        throw new Error('INPUT_ERROR: ' + detail);
      }
      // 500 系 / その他は BACKEND_DOWN として扱う (旧挙動互換)
      throw new Error('BACKEND_DOWN');
    }

    const signupData = await signupRes.json();

    // checkout-success.html で「メール届きませんでしたか?」UI を出すために
    // signupData.email_sent + email を sessionStorage に渡す。
    // (success_url は Stripe の {CHECKOUT_SESSION_ID} を含むため、URL 改変では渡せない場面がある)
    try {
      // 購入種別 (checkout-success.html の文言分岐用)。success_url の ?purchase= が正だが、
      // デプロイ跨ぎの旧 Stripe セッション完了など param が無い場合の fallback として
      // ここでも正しい種別を書く。extend opt-in (21日 trial → 自動課金) と
      // 即時本契約 (#immediateBtn / student_addon) は体験と案内が真逆になるため区別必須。
      const _extOptIn = !!document.getElementById('enableCardExtension')?.checked;
      const _planMeta = (document.querySelector('input[name="plan"]:checked')?.value || window.__urlPlanOverride || 'founder_special');
      const _purchaseTypeMeta = (_planMeta === 'student_addon') ? 'student_addon'
        : (_immediateSubmit ? 'monthly' : (_extOptIn ? 'trial_extended' : 'trial'));
      sessionStorage.setItem('ai_juku_signup_meta', JSON.stringify({
        email: payload.email,
        name: payload.name,
        student_id: signupData.student_id || null,
        email_sent: !!signupData.email_sent,
        is_carrier_email: isCarrierEmail(payload.email),
        purchase_type: _purchaseTypeMeta,
        ts: Date.now(),
      }));
    } catch (_e) { /* sessionStorage が無効でも遷移自体は続行 */ }

    // 2. 14日間 完全無料体験 (バックエンドが FOUNDER_TRIAL_PRICE=0 を検出すると
    //    Stripe をスキップして即座に checkout-success.html へ遷移する)。
    //    継続は別途 upgrade.html で本契約。
    // 招待コード (通塾生 student_addon プラン用) を取得して送信
    // 2026-05-07: URL params だけでなく入力欄 #inviteCode の手入力も受け付ける (塾長指示)
    // 体験フローでは backend は invite_code を保管・本契約時に検証 (memory: feedback_student_invite_link)
    // 🎁 2026-05-19 集客 funnel #4: クレカ登録 +7 日延長 opt-in
    const enableCardExt = !!document.getElementById('enableCardExtension')?.checked;
    const checkoutBody = {
      email: payload.email,
      name: payload.name,
      student_id: signupData.student_id,
      enable_card_for_extension: enableCardExt,  // true: Stripe Subscription 21 日 trial / false: free 14 日
    };
    // Reviewer B H2: 全角空白も除去 (DM コピペで全角混入対策)
    const inviteFromInput = (document.getElementById('inviteCode')?.value || '')
      .trim()
      .replace(/[\s　]+/g, '');
    const inviteCode = inviteFromInput || window.__inviteToken || '';
    // payload に plan ヒントを送る (= server side で student_addon の場合に invite_code 必須化)
    const selectedPlanForBody = (document.querySelector('input[name="plan"]:checked')?.value || window.__urlPlanOverride || 'founder_special');
    if (selectedPlanForBody) {
      checkoutBody.plan = selectedPlanForBody;
    }
    // 通塾生プラン選択時は招待コード必須 (2026-05-07: 不正契約防止)
    const selectedPlanGuard = (document.querySelector('input[name="plan"]:checked')?.value || window.__urlPlanOverride || 'founder_special');
    if (selectedPlanGuard === 'student_addon' && !inviteCode) {
      alert('🎓 通塾生プランをご利用には、塾長から発行された招待コードが必要です。\n\n「🎓 通塾生 招待コード」欄に DM で受け取ったコードをご入力ください。\nお持ちでない方は塾長 (Instagram/Threads DM) までお問い合わせください。');
      const inviteEl = document.getElementById('inviteCode');
      if (inviteEl) { inviteEl.focus(); inviteEl.scrollIntoView({ block: 'center', behavior: 'smooth' }); }
      throw new Error('INVITE_CODE_REQUIRED');
    }
    if (inviteCode) {
      checkoutBody.invite_code = inviteCode;
    }
    // 🚨 2026-05-07 致命修正: student_addon は trial-checkout (無料体験) ではなく
    // /api/stripe/checkout (即課金 ¥5,000/月) に流す。これまで student_addon 選択しても
    // 無料体験ループに陥り、本契約に至れない致命バグ (塾長指摘・森澤さん事故時)。
    // 体験中の trial student (signupData.student_id) は維持されるので学習履歴は継承される。
    // 🚀 2026-05-29 塾長指示: 体験をスキップして即時本契約で始める第2導線。
    //   #immediateBtn が window.__skipTrialImmediate=true を立てて submit すると
    //   一般プラン (founder_special 等) でも即課金 /api/stripe/checkout に流す。
    //   (体験 14日無料はデフォルト主導線として維持・#submitBtn 経由は従来通り trial)
    const isPaidPlan = (selectedPlanForBody === 'student_addon') || _immediateSubmit;
    const checkoutEndpoint = isPaidPlan ? '/api/stripe/checkout' : '/api/stripe/trial-checkout';
    // 🛡️ 2026-05-21 P0-2: trial-checkout は Railway cold-start で 5-16s かかる事があるため
    // timeout は 25 秒に設定 (signup より長め)。
    const checkoutRes = await fetchWithTimeout(`${API_BASE}${checkoutEndpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(checkoutBody),
    }, 25000);
    // 創設メンバー50名達成時は403で停止する。URL直打ち経由の51名目以降をブロック。
    if (checkoutRes.status === 403) {
      const errData = await checkoutRes.json().catch(() => ({ detail: '募集終了' }));
      throw new Error(errData.detail || '創設メンバーの募集は終了しました');
    }
    // 🛡️ 2026-05-21 P0-1: 429 / 422 / 400 を具体エラー表示
    if (checkoutRes.status === 429) {
      const detail = await readErrorDetail(checkoutRes,
        'ただ今混み合っています。5 分ほど待ってから再度お試しください。');
      throw new Error('RATE_LIMITED: ' + detail);
    }
    if (checkoutRes.status === 422 || checkoutRes.status === 400) {
      const detail = await readErrorDetail(checkoutRes,
        '入力内容に不備があります。プラン選択 / 招待コードをご確認ください。');
      throw new Error('INPUT_ERROR: ' + detail);
    }
    if (!checkoutRes.ok) {
      throw new Error('BACKEND_DOWN');
    }
    const checkoutData = await checkoutRes.json();

    if (checkoutData.checkout_url) {
      // Track event before redirect
      fetch(`${API_BASE}/api/track`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'checkout_initiated', props: { plan } }),
      }).catch(() => {});

      window.location.href = checkoutData.checkout_url;
    } else {
      throw new Error('決済セッションの作成に失敗しました');
    }
  } catch (err) {
    loadingBox.style.display = 'none';
    submitBtn.disabled = false;
    // 🚀 即時本契約フラグをリセット + 第2ボタンの状態復帰 (失敗が次回 submit に残らないように)
    window.__skipTrialImmediate = false;
    const _immBtn = document.getElementById('immediateBtn');
    if (_immBtn) {
      _immBtn.disabled = false;
      _immBtn.textContent = '⚡ 体験をスキップして今すぐ本契約で始める →';
    }
    // plan に応じてボタン文言を復元 (student_addon は本契約の文言)
    const errPlan = (document.querySelector('input[name="plan"]:checked')?.value || window.__urlPlanOverride || 'founder_special');
    const _ext = !!document.getElementById('enableCardExtension')?.checked;
    submitBtn.textContent = (errPlan === 'student_addon')
      ? '💳 ¥5,000/月で登録する →'
      : (_ext ? '🎁 14日間 完全無料体験を開始する (クレカ登録) →' : '🎁 7日間 無料体験を開始する →');

    // BACKEND_DOWN 時の「自動で成功画面へ進行」を削除。
    // 以前は決済せずに localStorage に学生を作って「成功」画面へ遷移していたが、
    // 攻撃者がバックエンドを一時ブロックすれば無料でアカウント作成できてしまう上、
    // 保護者が「決済したつもり」の誤認を起こす（クレーム直結）。常にエラーのみ表示。
    const supportLine = '<br><br>📞 お困りの場合は <a href="mailto:info@trillion-ai-juku.com" style="color:var(--primary-light);">info@trillion-ai-juku.com</a> まで。';

    // 🛡️ 2026-05-21 P0-1/P0-2: 具体エラー pattern を user に表示 (silent BACKEND_DOWN 解消)
    const msg = (err && err.message) || '';
    const isAbort = (err && err.name === 'AbortError') || msg.includes('aborted');
    if (msg.startsWith('RATE_LIMITED:')) {
      const detail = msg.slice('RATE_LIMITED:'.length).trim();
      errorBox.innerHTML = `
        <strong>⏱ ただ今混み合っています</strong><br>
        ${_esc(detail)}<br>
        <strong>5 分ほど待ってから</strong>もう一度「無料体験を開始する」ボタンをお押しください。${supportLine}
      `;
      errorBox.style.display = 'block';
    } else if (msg.startsWith('INPUT_ERROR:')) {
      const detail = msg.slice('INPUT_ERROR:'.length).trim();
      errorBox.innerHTML = `
        <strong>⚠️ 入力内容に不備があります</strong><br>
        ${_esc(detail)}${supportLine}
      `;
      errorBox.style.display = 'block';
    } else if (isAbort) {
      // P0-2: timeout 経過時 (iPhone Safari 背景タブ stall 等)
      errorBox.innerHTML = `
        <strong>⏱ 接続が遅延しています</strong><br>
        ネットワークが不安定か、サーバ起動中の可能性があります。<br>
        <strong>もう一度「無料体験を開始する」ボタン</strong>を押してください。${supportLine}
      `;
      errorBox.style.display = 'block';
    } else if (msg === 'BACKEND_DOWN' || msg.includes('Failed to fetch') || msg.includes('NetworkError')) {
      errorBox.innerHTML = `
        <strong>⚠️ 決済サービスに接続できませんでした</strong><br>
        ただ今混み合っているか、ネットワークが不安定な可能性があります。<br>
        <strong>もう一度「無料体験を開始する」ボタンを押してお試しいただくか</strong>、少し時間をおいて再度お試しください。${supportLine}
      `;
      errorBox.style.display = 'block';
    } else if (msg.includes('募集終了')) {
      errorBox.innerHTML = `
        <strong>🙏 創設メンバー50名の募集は終了しました</strong><br>
        通常プランからお申込みいただけます。${supportLine}
      `;
      errorBox.style.display = 'block';
    } else if (msg === 'INVITE_CODE_REQUIRED') {
      // すでに alert で案内済み (招待コード欄に focus)
    } else {
      errorBox.innerHTML = `<strong>エラー:</strong> ${_esc(msg || '不明なエラー')}<br>もう一度お試しください。${supportLine}`;
      errorBox.style.display = 'block';
    }
  } finally {
    // 🛡️ 2026-05-21 P0-3: cache-purge.js race フラグを必ずリセット
    window.__checkout_in_flight = false;
  }
});
