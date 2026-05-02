// ==========================================================================
// 🎯 Mock Exam (完全模試) — Frontend
// ==========================================================================

(function() {
  const BACKEND_URL = window.location.hostname === 'localhost' && window.location.port === '8090'
    ? 'http://localhost:8000'
    : window.location.origin;

  // 状態
  let currentSession = null;
  let answers = {};
  let timerInterval = null;
  let endsAt = null;

  // === Step 1: テンプレート読み込み ===
  async function loadTemplates() {
    const grid = document.getElementById('meTemplates');
    try {
      const res = await fetch(`${BACKEND_URL}/api/mock-exam/templates`);
      const data = await res.json();
      grid.innerHTML = data.templates.map(t => `
        <div class="me-template-card" data-exam-type="${t.exam_type}">
          <div class="me-template-label">${t.label}</div>
          <div class="me-template-meta">
            <span>⏱ ${t.duration_min} 分</span>
            <span>📊 満点 ${t.max_score}</span>
            <span>📝 ${t.section_count} セクション</span>
          </div>
          <button class="btn-primary me-template-start" data-exam-type="${t.exam_type}">受験を開始 →</button>
        </div>
      `).join('');
      grid.querySelectorAll('.me-template-start').forEach(btn => {
        btn.addEventListener('click', (e) => startExam(e.target.dataset.examType));
      });
    } catch (e) {
      grid.innerHTML = `<p style="color:#ef4444;">テンプレート読み込みに失敗しました: ${e.message}</p>`;
    }
  }

  // === Step 2: 模試開始 ===
  async function startExam(examType) {
    const grid = document.getElementById('meTemplates');
    grid.innerHTML = '<p>模試を生成中...</p>';
    try {
      const studentId = localStorage.getItem('aj_current_student_id');
      const res = await fetch(`${BACKEND_URL}/api/mock-exam/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ exam_type: examType, student_id: studentId ? parseInt(studentId) : null }),
      });
      if (!res.ok) throw new Error(`Generate failed: ${res.status}`);
      const data = await res.json();
      if (typeof window.track === 'function') window.track('mock_exam_start', { exam_type: examType });
      currentSession = data;
      answers = {};
      renderExam(data);
    } catch (e) {
      grid.innerHTML = `<p style="color:#ef4444;">模試生成に失敗: ${e.message}</p>`;
      console.error(e);
    }
  }

  function renderExam(data) {
    document.getElementById('meSetup').style.display = 'none';
    document.getElementById('meExam').style.display = 'block';
    document.getElementById('meResult').style.display = 'none';
    document.getElementById('meTitle').textContent = data.label;

    // タイマー開始
    endsAt = Date.now() + data.duration_min * 60 * 1000;
    updateTimer();
    if (timerInterval) clearInterval(timerInterval);
    timerInterval = setInterval(updateTimer, 1000);

    // セクション・問題描画
    const wrap = document.getElementById('meSections');
    wrap.innerHTML = data.sections.map((sec, sIdx) => {
      const qsHtml = sec.questions.map((q, qIdx) => renderQuestion(sec, q, sIdx, qIdx)).join('');
      return `
        <section class="me-section-block">
          <h3>セクション ${sIdx + 1}: ${sec.name} <span class="me-section-meta">(各 ${sec.points_per_question}点)</span></h3>
          ${qsHtml}
        </section>
      `;
    }).join('');

    // 入力監視で進捗更新
    wrap.addEventListener('change', onAnswerChange);
    updateProgress();
    window.scrollTo(0, 0);
  }

  function renderQuestion(sec, q, sIdx, qIdx) {
    const passage = q.passage ? `<div class="me-passage"><pre>${escapeHtml(q.passage)}</pre></div>` : '';
    const audio = q.audio_script ? `<details class="me-audio-script"><summary>📢 音声スクリプト</summary><pre>${escapeHtml(q.audio_script)}</pre></details>` : '';
    const prompt = q.prompt ? `<div class="me-prompt"><strong>${escapeHtml(q.prompt)}</strong></div>` : '';
    const yearLabel = q.year_simulated || q.univ_simulated ? `<div class="me-q-meta">${escapeHtml(q.univ_simulated || '')} ${q.year_simulated || ''}</div>` : '';

    const subQs = (q.questions || []).map(sq => {
      if (sq.type === 'multiple_choice') {
        const choices = (sq.choices || []).map((ch, idx) => `
          <label class="me-choice">
            <input type="radio" name="q_${q.exam_question_id}_${sq.id}" value="${idx}" data-eq="${q.exam_question_id}" data-sub="${sq.id}">
            <span class="me-choice-letter">${String.fromCharCode(65 + idx)}.</span>
            <span class="me-choice-text">${escapeHtml(ch)}</span>
          </label>
        `).join('');
        return `
          <div class="me-subq">
            <div class="me-subq-stem">${escapeHtml(sq.stem)}</div>
            <div class="me-choices">${choices}</div>
          </div>
        `;
      } else {
        // essay 型は今回は表示のみ (記述採点なし) — placeholder
        return `
          <div class="me-subq">
            <div class="me-subq-stem">${escapeHtml(sq.stem)}</div>
            <textarea rows="4" placeholder="(記述問題は採点対象外・ベータ機能)"></textarea>
          </div>
        `;
      }
    }).join('');

    return `
      <article class="me-question">
        ${yearLabel}
        ${prompt}
        ${passage}
        ${audio}
        ${subQs}
      </article>
    `;
  }

  function onAnswerChange(e) {
    if (e.target.matches('input[type="radio"]')) {
      const eq = e.target.dataset.eq;
      const sub = e.target.dataset.sub;
      answers[`${eq}_${sub}`] = e.target.value;
      updateProgress();
    }
  }

  function updateProgress() {
    if (!currentSession) return;
    let total = 0;
    currentSession.sections.forEach(sec => {
      sec.questions.forEach(q => {
        (q.questions || []).forEach(sq => {
          if (sq.type === 'multiple_choice') total += 1;
        });
      });
    });
    const done = Object.keys(answers).length;
    document.getElementById('meProgressLabel').textContent = `${done} / ${total} 問完了`;
    document.getElementById('meProgressFill').style.width = total ? `${(done / total) * 100}%` : '0%';
  }

  function updateTimer() {
    const remaining = Math.max(0, endsAt - Date.now());
    const min = Math.floor(remaining / 60000);
    const sec = Math.floor((remaining % 60000) / 1000);
    document.getElementById('meTimer').textContent = `${String(min).padStart(2,'0')}:${String(sec).padStart(2,'0')}`;
    if (remaining <= 0) {
      clearInterval(timerInterval);
      document.getElementById('meTimer').textContent = '時間切れ';
      submitExam();
    }
  }

  // === Step 3: 採点・結果表示 ===
  async function submitExam() {
    if (!currentSession) return;
    const submitBtn = document.getElementById('meSubmitBtn');
    submitBtn.disabled = true;
    submitBtn.textContent = '採点中...';
    if (timerInterval) clearInterval(timerInterval);
    try {
      const res = await fetch(`${BACKEND_URL}/api/mock-exam/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: currentSession.session_id, answers }),
      });
      if (!res.ok) throw new Error(`Submit failed: ${res.status}`);
      const data = await res.json();
      if (typeof window.track === 'function') window.track('mock_exam_submit', { exam_type: currentSession.exam_type, percentage: data.percentage });
      renderResult(data);
    } catch (e) {
      alert(`採点エラー: ${e.message}`);
      submitBtn.disabled = false;
      submitBtn.textContent = '📊 採点する';
    }
  }

  function renderResult(data) {
    document.getElementById('meExam').style.display = 'none';
    document.getElementById('meResult').style.display = 'block';
    document.getElementById('meScoreTotal').textContent = data.score_total;
    document.getElementById('meScoreMax').textContent = data.score_max;
    document.getElementById('meScorePct').textContent = data.percentage;
    document.getElementById('meDeviation').textContent = data.deviation_estimate;

    // セクション別
    const list = document.getElementById('meSectionList');
    list.innerHTML = (data.section_scores || []).map(s => `
      <div class="me-section-row">
        <span class="me-section-name">${escapeHtml(s.name)}</span>
        <span class="me-section-bar-bg"><span class="me-section-bar-fill" style="width:${s.pct}%;"></span></span>
        <span class="me-section-pct">${s.pct}% (${s.got}/${s.max})</span>
      </div>
    `).join('');

    // シェア URL
    const shareText = `AI学習コーチ塾の完全模試で偏差値 ${data.deviation_estimate} (${data.percentage}%) でした! AI が動的に生成する模試で本番想定の演習ができます`;
    const shareUrl = window.location.origin + '/lp.html';
    document.getElementById('meShareTwitter').onclick = () => {
      window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(shareText)}&url=${encodeURIComponent(shareUrl)}`, '_blank');
      if (typeof window.track === 'function') window.track('mock_exam_share', { platform: 'twitter' });
    };
    document.getElementById('meShareThreads').onclick = () => {
      window.open(`https://threads.net/intent/post?text=${encodeURIComponent(shareText + ' ' + shareUrl)}`, '_blank');
      if (typeof window.track === 'function') window.track('mock_exam_share', { platform: 'threads' });
    };

    document.getElementById('meRetryBtn').onclick = () => {
      document.getElementById('meSetup').style.display = 'block';
      document.getElementById('meResult').style.display = 'none';
      currentSession = null;
      answers = {};
      loadTemplates();
    };

    window.scrollTo(0, 0);
  }

  function escapeHtml(s) {
    if (s == null) return '';
    return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }

  // === 初期化 ===
  document.addEventListener('DOMContentLoaded', () => {
    loadTemplates();
    document.getElementById('meSubmitBtn').addEventListener('click', () => {
      const total = Object.keys(answers).length;
      if (total === 0) {
        alert('まだ何も解答されていません。');
        return;
      }
      if (confirm('採点しますか? (途中提出も可能です)')) submitExam();
    });
  });
})();
