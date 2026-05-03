// ==========================================================================
// 📚 AI 単語帳 — Frontend (4 択クイズ + Leitner SRS)
// 塾長指示 2026-05-03: 4 択・同品詞縛り・自動詞/他動詞・品詞ラベル表示
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
  let answered = false; // 現在の単語が既に回答済みか

  // === Web Speech API 音声読み上げ ===
  function speak(text, rate = 0.9) {
    if (!('speechSynthesis' in window) || !text) return;
    try {
      window.speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(text);
      u.lang = 'en-US';
      u.rate = rate;
      u.pitch = 1.0;
      window.speechSynthesis.speak(u);
    } catch (e) { console.warn('TTS failed', e); }
  }

  function getStudentId() {
    const id = localStorage.getItem('aj_current_student_id');
    return id ? parseInt(id) : 1;
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

  // === キュー取得 (4 択クイズ endpoint) ===
  async function loadQueue(level, univ) {
    const studentId = getStudentId();
    const fetchLimit = univ ? 60 : 20;
    const params = new URLSearchParams({ student_id: studentId, limit: fetchLimit });
    if (level) params.set('level', level);
    if (univ) params.set('univ', univ);
    try {
      const res = await fetch(`${BACKEND_URL}/api/vocab/quiz?${params}`);
      if (!res.ok) throw new Error(`Quiz fetch failed: ${res.status}`);
      const data = await res.json();
      queue = (data.quiz || []).slice(0, 20);
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

  function labelLevel(lv) {
    const map = {
      'eiken_g3': '英検3級', 'eiken_gp2': '英検準2級', 'eiken_g2': '英検2級',
      'eiken_gp1': '英検準1級', 'eiken_g1': '英検1級',
      'kyotsu': '共通テスト', 'todai_kyodai': '難関国立',
    };
    return map[lv] || lv || '--';
  }

  // === カード描画 (4 択 UI) ===
  function renderCard() {
    if (queueIndex >= queue.length) {
      showComplete();
      return;
    }
    const w = queue[queueIndex];
    answered = false;
    document.getElementById('vcQueueCount').textContent = `単語 ${queueIndex + 1}/${queue.length}`;
    document.getElementById('vcCardWord').textContent = w.word;

    // 品詞バッジ (動詞/名詞/形容詞 ...)
    const posEl = document.getElementById('vcCardPos');
    posEl.textContent = w.pos_label_jp || '';
    posEl.style.display = w.pos_label_jp ? '' : 'none';

    // 自動詞/他動詞バッジ
    const vtEl = document.getElementById('vcCardVt');
    if (w.transitivity && w.transitivity_label_jp) {
      vtEl.textContent = w.transitivity_label_jp;
      vtEl.dataset.kind = w.transitivity; // CSS で色分け (vt/vi/vt+vi)
      vtEl.style.display = '';
    } else {
      vtEl.style.display = 'none';
    }

    // 4 択ボタン
    const choices = w.choices || [];
    const correctIdx = w.correct_index;
    document.querySelectorAll('.vc-choice').forEach((btn, i) => {
      btn.textContent = (i + 1) + '. ' + (choices[i] || '');
      btn.classList.remove('correct', 'wrong', 'disabled');
      btn.disabled = false;
      btn.dataset.correct = (i === correctIdx) ? '1' : '0';
    });

    // フィードバック非表示
    document.getElementById('vcQuizFeedback').style.display = 'none';
    document.getElementById('vcCardExample').textContent = w.example_en || '';
    document.getElementById('vcCardExampleJp').textContent = w.example_jp || '';

    document.getElementById('vcCurrentBox').textContent = `Box: ${w.box || 0} (${w.status === 'new' ? '未学習' : '復習'})`;
    document.getElementById('vcCurrentLevel').textContent = `レベル: ${labelLevel(w.level)}`;

    // 自動読み上げ
    const autoSpeak = document.getElementById('vcAutoSpeak');
    if (autoSpeak && autoSpeak.checked) {
      setTimeout(() => speak(w.word, 0.85), 150);
    }
  }

  // === 選択肢クリック ===
  function onChoiceClick(idx) {
    if (answered) return;
    answered = true;
    const w = queue[queueIndex];
    if (!w) return;
    const correctIdx = w.correct_index;
    const isCorrect = idx === correctIdx;

    document.querySelectorAll('.vc-choice').forEach((btn, i) => {
      btn.disabled = true;
      btn.classList.add('disabled');
      if (i === correctIdx) btn.classList.add('correct');
      else if (i === idx) btn.classList.add('wrong');
    });

    // フィードバック表示
    const fb = document.getElementById('vcQuizFeedback');
    fb.style.display = '';
    const status = document.getElementById('vcFeedbackStatus');
    status.innerHTML = isCorrect
      ? '<span style="color:#10b981;font-weight:800;">✅ 正解!</span> '
        + `<span style="font-size:0.85em;color:#94a3b8;">(${w.pos_label_jp || ''}${w.transitivity_label_jp ? ' / ' + w.transitivity_label_jp : ''})</span>`
      : '<span style="color:#ef4444;font-weight:800;">❌ 不正解</span> '
        + `<span style="font-size:0.95em;color:#cbd5e1;">正解: ${w.meaning_jp}</span>`;

    // 例文の自動読み上げ
    const autoSpeak = document.getElementById('vcAutoSpeak');
    if (autoSpeak && autoSpeak.checked && w.example_en) {
      setTimeout(() => speak(w.example_en, 0.95), 250);
    }

    // grade を SRS バックエンドに送信
    const studentId = getStudentId();
    fetch(`${BACKEND_URL}/api/vocab/grade`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ student_id: studentId, word_id: w.id, knew: isCorrect }),
    }).catch(e => console.warn('grade failed', e));

    if (typeof window.track === 'function') window.track('vocab_quiz_answer', { knew: isCorrect, level: w.level, pos: w.pos });

    reviewedCount += 1;
    if (isCorrect) correctCount += 1;
  }

  function nextCard() {
    queueIndex += 1;
    renderCard();
  }

  function showComplete() {
    document.getElementById('vcReview').style.display = 'none';
    document.getElementById('vcComplete').style.display = 'block';
    document.getElementById('vcReviewedCount').textContent = reviewedCount;
    document.getElementById('vcCorrectCount').textContent = correctCount;
  }

  async function startReview() {
    const ok = await loadQueue(currentLevel, currentUniv);
    if (!ok) return;
    document.getElementById('vcSetup').style.display = 'none';
    document.getElementById('vcReview').style.display = 'block';
    document.getElementById('vcComplete').style.display = 'none';
    if (typeof window.track === 'function') window.track('vocab_session_start', { level: currentLevel, mode: 'quiz4' });
    renderCard();
  }

  document.addEventListener('DOMContentLoaded', () => {
    loadStats();

    document.querySelectorAll('.vc-level-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.vc-level-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentLevel = btn.dataset.level || '';
      });
    });
    document.querySelector('.vc-level-btn[data-level=""]').classList.add('active');

    document.querySelectorAll('.vc-univ-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.vc-univ-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentUniv = btn.dataset.univ || '';
      });
    });

    document.getElementById('vcStartBtn').addEventListener('click', startReview);

    // 4 択ボタン bind
    document.querySelectorAll('.vc-choice').forEach((btn) => {
      btn.addEventListener('click', () => {
        const idx = parseInt(btn.dataset.idx, 10);
        onChoiceClick(idx);
      });
    });
    // キーボード 1-4 で選択
    document.addEventListener('keydown', (e) => {
      if (document.getElementById('vcReview').style.display === 'none') return;
      if (answered && e.key === 'Enter') { nextCard(); return; }
      if (['1','2','3','4'].includes(e.key)) onChoiceClick(parseInt(e.key,10) - 1);
    });

    document.getElementById('vcSpeakBtn').addEventListener('click', () => {
      const w = queue[queueIndex];
      if (w) speak(w.word, 0.85);
    });
    document.getElementById('vcSpeakExampleBtn').addEventListener('click', () => {
      const w = queue[queueIndex];
      if (w && w.example_en) speak(w.example_en, 0.95);
    });
    document.getElementById('vcNextBtn').addEventListener('click', nextCard);
    document.getElementById('vcExitBtn').addEventListener('click', () => {
      if (confirm('クイズを終了しますか?')) showComplete();
    });
    document.getElementById('vcContinueBtn').addEventListener('click', () => {
      document.getElementById('vcComplete').style.display = 'none';
      document.getElementById('vcSetup').style.display = 'block';
      loadStats();
    });
  });
})();
