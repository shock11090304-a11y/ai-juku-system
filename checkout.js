// Checkout page: Stripe integration
const API_BASE = window.location.origin.includes(':8090')
  ? 'http://localhost:8000'  // dev: FastAPI on :8000, frontend on :8090
  : window.location.origin;  // prod: same origin

const PLAN_INFO = {
  founder1:  { name: '🎁 1期生プラン (永年¥25,000)', price: 25000 },
  standard:  { name: 'スタンダード',     price: 24980 },
  premium:   { name: 'プレミアム',       price: 39800 },
  family:    { name: '家族プラン（最大3名）', price: 59800 },
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
  document.querySelector(`input[value="${params.get('plan')}"]`).checked = true;
}
if (params.get('email')) document.getElementById('email').value = params.get('email');
if (params.get('lastName')) document.getElementById('lastName').value = params.get('lastName');
if (params.get('firstName')) document.getElementById('firstName').value = params.get('firstName');
if (params.get('grade')) document.getElementById('grade').value = params.get('grade');
if (params.get('goal')) document.getElementById('goal').value = params.get('goal');

updateSummary();
document.querySelectorAll('input[name="plan"]').forEach(r => r.addEventListener('change', updateSummary));

document.getElementById('checkoutForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const submitBtn = document.getElementById('submitBtn');
  const errorBox = document.getElementById('errorBox');
  const loadingBox = document.getElementById('loadingBox');

  const plan = document.querySelector('input[name="plan"]:checked').value;
  const lastName = (document.getElementById('lastName').value || '').trim();
  const firstName = (document.getElementById('firstName').value || '').trim();
  if (!lastName || !firstName) {
    errorBox.textContent = 'フルネーム（姓と名の両方）を入力してください。';
    errorBox.style.display = 'block';
    submitBtn.disabled = false;
    return;
  }
  const payload = {
    plan,
    name: `${lastName}${firstName}`,
    email: document.getElementById('email').value,
    grade: document.getElementById('grade').value,
    goal: document.getElementById('goal').value,
  };

  submitBtn.disabled = true;
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

    // 2. 体験用 ¥1,980 単発決済（サブスク無し・自動課金なし）
    //    継続は別途 upgrade.html で本契約。
    const checkoutRes = await fetch(`${API_BASE}/api/stripe/trial-checkout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: payload.email, name: payload.name, student_id: signupData.student_id }),
    });
    // 第1期生100名達成時は403で停止する。URL直打ち経由の101名目以降をブロック。
    if (checkoutRes.status === 403) {
      const errData = await checkoutRes.json().catch(() => ({ detail: '募集終了' }));
      throw new Error(errData.detail || '第1期生の募集は終了しました');
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

    // BACKEND_DOWN 時の「自動で成功画面へ進行」を削除。
    // 以前は決済せずに localStorage に学生を作って「成功」画面へ遷移していたが、
    // 攻撃者がバックエンドを一時ブロックすれば無料でアカウント作成できてしまう上、
    // 保護者が「決済したつもり」の誤認を起こす（クレーム直結）。常にエラーのみ表示。
    if (err.message === 'BACKEND_DOWN' || (err.message || '').includes('Failed to fetch')) {
      errorBox.innerHTML = `
        <strong>⚠️ 決済サービスに接続できませんでした</strong><br>
        ただ今混み合っているか、ネットワークが不安定な可能性があります。<br>
        少し時間をおいて再度お試しいただくか、塾までお問い合わせください。
      `;
      errorBox.style.display = 'block';
    } else {
      errorBox.textContent = `エラー: ${err.message}`;
      errorBox.style.display = 'block';
    }
  }
});
