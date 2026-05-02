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
  let currentUniv = '';
  let reviewedCount = 0;
  let correctCount = 0;

  // === Web Speech API 音声読み上げ ===
  function speak(text, rate = 0.9) {
    if (!('speechSynthesis' in window) || !text) return;
    try {
      window.speechSynthesis.cancel(); // 重複防止
      const u = new SpeechSynthesisUtterance(text);
      u.lang = 'en-US';
      u.rate = rate;
      u.pitch = 1.0;
      window.speechSynthesis.speak(u);
    } catch (e) { console.warn('TTS failed', e); }
  }

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
  async function loadQueue(level, univ) {
    const studentId = getStudentId();
    // 大学指定時は limit を多めに取得し、tags で client-side filter
    const fetchLimit = univ ? 100 : 20;
    const params = new URLSearchParams({ student_id: studentId, limit: fetchLimit });
    if (level) params.set('level', level);
    try {
      const res = await fetch(`${BACKEND_URL}/api/vocab/queue?${params}`);
      if (!res.ok) throw new Error(`Queue fetch failed: ${res.status}`);
      const data = await res.json();
      let all = data.queue || [];
      // 大学タグフィルタ (tags に "univ:todai" が含まれる単語のみ抽出)
      if (univ) {
        const wantTag = `univ:${univ}`;
        all = all.filter(w => (w.tags || '').split(',').map(t => t.trim()).includes(wantTag));
      }
      queue = all.slice(0, 20);
      queueIndex = 0;
      reviewedCount = 0;
      correctCount = 0;
      currentLevel = level;
      currentUniv = univ;
      if (queue.length === 0) {
        const msg = univ
          ? `${univ.toUpperCase()} 頻出単語の在庫がまだ少ないです。別大学/全レベルでお試しください。`
          : '現在復習対象の単語がありません。別レベルを選ぶか、新規単語の追加をお待ちください。';
        alert(msg);
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
    // 自動読み上げ
    const autoSpeak = document.getElementById('vcAutoSpeak');
    if (autoSpeak && autoSpeak.checked) {
      setTimeout(() => speak(w.word, 0.85), 150);
    }
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
    const ok = await loadQueue(currentLevel, currentUniv);
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

    // 大学選択
    document.querySelectorAll('.vc-univ-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.vc-univ-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentUniv = btn.dataset.univ || '';
      });
    });

    document.getElementById('vcStartBtn').addEventListener('click', startReview);
    document.getElementById('vcShowBtn').addEventListener('click', () => {
      document.getElementById('vcCardFront').style.display = 'none';
      document.getElementById('vcCardBack').style.display = '';
      // 例文の自動読み上げ
      const autoSpeak = document.getElementById('vcAutoSpeak');
      if (autoSpeak && autoSpeak.checked) {
        const w = queue[queueIndex];
        if (w && w.example_en) setTimeout(() => speak(w.example_en, 0.95), 200);
      }
    });
    // 手動読み上げボタン
    document.getElementById('vcSpeakBtn').addEventListener('click', () => {
      const w = queue[queueIndex];
      if (w) speak(w.word, 0.85);
    });
    document.getElementById('vcSpeakExampleBtn').addEventListener('click', () => {
      const w = queue[queueIndex];
      if (w && w.example_en) speak(w.example_en, 0.95);
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
