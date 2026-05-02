// ==========================================================================
// 📚 AI 単語帳 — Frontend (Leitner SRS)
// ==========================================================================

(function() {
  const BACKEND_URL = window.location.hostname === 'localhost' && window.location.port === '8090'
    ? 'http://localhost:8000'
    : window.location.origin;

  let queue = [];
  let queueIndex = 0;
  let currentLevel = '';
  let reviewedCount = 0;
  let correctCount = 0;

  function getStudentId() {
    const id = localStorage.getItem('aj_current_student_id');
    return id ? parseInt(id) : 1; // デフォルト: 体験ユーザー想定で id=1
  }

  // === 統計取得 ===
  async function loadStats() {
    try {
      const studentId = getStudentId();
      const res = await fetch(`${BACKEND_URL}/api/vocab/stats?student_id=${studentId}`);
      if (!res.ok) return;
      const s = await res.json();
      document.getElementById('vcStatsCard').style.display = '';
      document.getElementById('vcDueNow').textContent = s.due_now || 0;
      document.getElementById('vcMastered').textContent = s.mastered || 0;
      document.getElementById('vcAccuracy').textContent = (s.accuracy_percent || 0) + '%';
      document.getElementById('vcTotal').textContent = s.total_words_in_pool || 0;
    } catch (e) {
      console.warn('stats load failed', e);
    }
  }

  // === キュー取得 ===
  async function loadQueue(level) {
    const studentId = getStudentId();
    const params = new URLSearchParams({ student_id: studentId, limit: 20 });
    if (level) params.set('level', level);
    try {
      const res = await fetch(`${BACKEND_URL}/api/vocab/queue?${params}`);
      if (!res.ok) throw new Error(`Queue fetch failed: ${res.status}`);
      const data = await res.json();
      queue = data.queue || [];
      queueIndex = 0;
      reviewedCount = 0;
      correctCount = 0;
      currentLevel = level;
      if (queue.length === 0) {
        alert('現在復習対象の単語がありません。別レベルを選ぶか、新規単語の追加をお待ちください。');
        return false;
      }
      return true;
    } catch (e) {
      alert(`単語取得失敗: ${e.message}`);
      return false;
    }
  }

  // === カード描画 ===
  function renderCard() {
    if (queueIndex >= queue.length) {
      showComplete();
      return;
    }
    const w = queue[queueIndex];
    document.getElementById('vcQueueCount').textContent = `単語 ${queueIndex + 1}/${queue.length}`;
    document.getElementById('vcCardWord').textContent = w.word;
    document.getElementById('vcCardPos').textContent = w.pos || '';
    document.getElementById('vcCardMeaning').textContent = w.meaning_jp || '';
    document.getElementById('vcCardExample').textContent = w.example_en || '';
    document.getElementById('vcCardExampleJp').textContent = w.example_jp || '';
    document.getElementById('vcCurrentBox').textContent = `Box: ${w.box || 0} (${w.status === 'new' ? '未学習' : '復習'})`;
    document.getElementById('vcCurrentLevel').textContent = `レベル: ${labelLevel(w.level)}`;
    document.getElementById('vcCardFront').style.display = '';
    document.getElementById('vcCardBack').style.display = 'none';
  }

  function labelLevel(lv) {
    const map = {
      'eiken_g3': '英検3級', 'eiken_gp2': '英検準2級', 'eiken_g2': '英検2級',
      'eiken_gp1': '英検準1級', 'eiken_g1': '英検1級',
      'kyotsu': '共通テスト', 'todai_kyodai': '難関国立',
    };
    return map[lv] || lv || '--';
  }

  // === 自己評価 ===
  async function gradeCard(knew) {
    const w = queue[queueIndex];
    if (!w) return;
    const studentId = getStudentId();
    try {
      await fetch(`${BACKEND_URL}/api/vocab/grade`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ student_id: studentId, word_id: w.id, knew }),
      });
      if (typeof window.track === 'function') window.track('vocab_grade', { knew, level: w.level });
    } catch (e) {
      console.warn('grade failed', e);
    }
    reviewedCount += 1;
    if (knew) correctCount += 1;
    queueIndex += 1;
    renderCard();
  }

  function showComplete() {
    document.getElementById('vcReview').style.display = 'none';
    document.getElementById('vcComplete').style.display = 'block';
    document.getElementById('vcReviewedCount').textContent = reviewedCount;
    document.getElementById('vcCorrectCount').textContent = correctCount;
  }

  // === 開始ボタン ===
  async function startReview() {
    const ok = await loadQueue(currentLevel);
    if (!ok) return;
    document.getElementById('vcSetup').style.display = 'none';
    document.getElementById('vcReview').style.display = 'block';
    document.getElementById('vcComplete').style.display = 'none';
    if (typeof window.track === 'function') window.track('vocab_session_start', { level: currentLevel });
    renderCard();
  }

  // === 初期化 ===
  document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    // レベル選択
    document.querySelectorAll('.vc-level-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.vc-level-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentLevel = btn.dataset.level || '';
      });
    });
    // 全レベルをデフォルト active に
    document.querySelector('.vc-level-btn[data-level=""]').classList.add('active');

    document.getElementById('vcStartBtn').addEventListener('click', startReview);
    document.getElementById('vcShowBtn').addEventListener('click', () => {
      document.getElementById('vcCardFront').style.display = 'none';
      document.getElementById('vcCardBack').style.display = '';
    });
    document.getElementById('vcGradeYes').addEventListener('click', () => gradeCard(true));
    document.getElementById('vcGradeNo').addEventListener('click', () => gradeCard(false));
    document.getElementById('vcExitBtn').addEventListener('click', () => {
      if (confirm('復習を終了しますか?')) showComplete();
    });
    document.getElementById('vcContinueBtn').addEventListener('click', () => {
      document.getElementById('vcComplete').style.display = 'none';
      document.getElementById('vcSetup').style.display = 'block';
      loadStats();
    });
  });
})();
