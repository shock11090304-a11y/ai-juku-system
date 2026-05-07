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
window.__inviteToken = params.get('invite') || '';
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
    return;
  }
  if (!isValidEmailFormat(email)) {
    errorBox.textContent = '⚠️ メールアドレスの形式が正しくありません。 (例: parent@example.com)';
    errorBox.style.display = 'block';
    submitBtn.disabled = false;
    return;
  }
  // 生徒メールは任意。入力されていれば形式チェック
  if (studentEmail && !isValidEmailFormat(studentEmail)) {
    errorBox.textContent = '⚠️ 生徒様メールアドレスの形式が正しくありません。空欄でも構いません。';
    errorBox.style.display = 'block';
    submitBtn.disabled = false;
    return;
  }
  if (!grade) {
    errorBox.textContent = '⚠️ 学年を選択してください。';
    errorBox.style.display = 'block';
    submitBtn.disabled = false;
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

  const payload = {
    plan,
    name: `${lastName}${firstName}`,
    email,
    student_email: studentEmail,  // 任意 (空欄なら保護者メールのみ)
    grade,
    goal: document.getElementById('goal').value,
    ref: refCode || undefined,
  };

  submitBtn.disabled = true;
  submitBtn.textContent = '📮 送信中... (1〜2秒)';
  errorBox.style.display = 'none';
  loadingBox.style.display = 'block';

  try {
    // 1. Register trial (creates student record)
    const signupRes = await fetch(`${API_BASE}/api/trial/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!signupRes.ok) {
      // Backend not running - fall back to direct app
      throw new Error('BACKEND_DOWN');
    }

    const signupData = await signupRes.json();

    // checkout-success.html で「メール届きませんでしたか?」UI を出すために
    // signupData.email_sent + email を sessionStorage に渡す。
    // (success_url は Stripe の {CHECKOUT_SESSION_ID} を含むため、URL 改変では渡せない場面がある)
    try {
      sessionStorage.setItem('ai_juku_signup_meta', JSON.stringify({
        email: payload.email,
        name: payload.name,
        student_id: signupData.student_id || null,
        email_sent: !!signupData.email_sent,
        is_carrier_email: isCarrierEmail(payload.email),
        ts: Date.now(),
      }));
    } catch (_e) { /* sessionStorage が無効でも遷移自体は続行 */ }

    // 2. 7日間 完全無料体験 (バックエンドが FOUNDER_TRIAL_PRICE=0 を検出すると
    //    Stripe をスキップして即座に checkout-success.html へ遷移する)。
    //    継続は別途 upgrade.html で本契約。
    // 招待コード (通塾生 student_addon プラン用) を取得して送信
    // 2026-05-07: URL params だけでなく入力欄 #inviteCode の手入力も受け付ける (塾長指示)
    // 体験フローでは backend は invite_code を保管・本契約時に検証 (memory: feedback_student_invite_link)
    const checkoutBody = { email: payload.email, name: payload.name, student_id: signupData.student_id };
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
    const checkoutRes = await fetch(`${API_BASE}/api/stripe/trial-checkout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(checkoutBody),
    });
    // 創設メンバー50名達成時は403で停止する。URL直打ち経由の51名目以降をブロック。
    if (checkoutRes.status === 403) {
      const errData = await checkoutRes.json().catch(() => ({ detail: '募集終了' }));
      throw new Error(errData.detail || '創設メンバーの募集は終了しました');
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
    submitBtn.textContent = '🎁 7日間 無料体験を開始する →';

    // BACKEND_DOWN 時の「自動で成功画面へ進行」を削除。
    // 以前は決済せずに localStorage に学生を作って「成功」画面へ遷移していたが、
    // 攻撃者がバックエンドを一時ブロックすれば無料でアカウント作成できてしまう上、
    // 保護者が「決済したつもり」の誤認を起こす（クレーム直結）。常にエラーのみ表示。
    const supportLine = '<br><br>📞 お困りの場合は <a href="mailto:info@trillion-ai-juku.com" style="color:var(--primary-light);">info@trillion-ai-juku.com</a> まで。';
    if (err.message === 'BACKEND_DOWN' || (err.message || '').includes('Failed to fetch')) {
      errorBox.innerHTML = `
        <strong>⚠️ 決済サービスに接続できませんでした</strong><br>
        ただ今混み合っているか、ネットワークが不安定な可能性があります。<br>
        <strong>もう一度「無料体験を開始する」ボタンを押してお試しいただくか</strong>、少し時間をおいて再度お試しください。${supportLine}
      `;
      errorBox.style.display = 'block';
    } else if ((err.message || '').includes('募集終了')) {
      errorBox.innerHTML = `
        <strong>🙏 創設メンバー50名の募集は終了しました</strong><br>
        通常プランからお申込みいただけます。${supportLine}
      `;
      errorBox.style.display = 'block';
    } else {
      errorBox.innerHTML = `<strong>エラー:</strong> ${(err.message || '不明なエラー')}<br>もう一度お試しください。${supportLine}`;
      errorBox.style.display = 'block';
    }
  }
});
