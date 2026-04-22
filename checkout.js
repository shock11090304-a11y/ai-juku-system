// Checkout page: Stripe integration
const API_BASE = window.location.origin.includes(':8090')
  ? 'http://localhost:8000'  // dev: FastAPI on :8000, frontend on :8090
  : window.location.origin;  // prod: same origin

const PLAN_INFO = {
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
}

// Pre-fill from URL params (from LP link)
const params = new URLSearchParams(window.location.search);
if (params.get('plan') && PLAN_INFO[params.get('plan')]) {
  document.querySelector(`input[value="${params.get('plan')}"]`).checked = true;
}
if (params.get('email')) document.getElementById('email').value = params.get('email');
if (params.get('name')) document.getElementById('name').value = params.get('name');
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
  const payload = {
    plan,
    name: document.getElementById('name').value,
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

    // 2. Create Stripe Checkout Session
    const checkoutRes = await fetch(`${API_BASE}/api/stripe/checkout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ plan, email: payload.email, name: payload.name, student_id: signupData.student_id }),
    });
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

    if (err.message === 'BACKEND_DOWN' || err.message.includes('Failed to fetch')) {
      errorBox.innerHTML = `
        <strong>⚠️ デモモード</strong><br>
        バックエンドサーバーが起動していないため、実際の決済はスキップします。<br>
        <strong>仮登録して体験版を開始します...</strong>
      `;
      errorBox.style.display = 'block';
      // Save to localStorage as fallback
      const students = JSON.parse(localStorage.getItem('ai_juku_students') || '[]');
      const newStudent = {
        id: Date.now(),
        name: payload.name,
        grade: payload.grade,
        goal: payload.goal || '未設定',
        email: payload.email,
        plan,
        fee: PLAN_INFO[plan].price,
        trialStart: new Date().toISOString(),
        weeklyHours: 15,
        subjects: { 英語: 60, 数学: 60, 国語: 60 },
      };
      students.push(newStudent);
      localStorage.setItem('ai_juku_students', JSON.stringify(students));
      localStorage.setItem('ai_juku_current_student', JSON.stringify(newStudent.id));
      setTimeout(() => { window.location.href = 'checkout-success.html?session_id=demo'; }, 2000);
    } else {
      errorBox.textContent = `エラー: ${err.message}`;
      errorBox.style.display = 'block';
    }
  }
});
