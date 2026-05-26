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
      // 🛡️ IDOR fix 2026-05-26: session token あれば送る (backend で claims 経由 student_id 確定)
      // 未ログイン (token 無し) でも fetch 可能・backend がゲスト session として処理
      const sessionToken = localStorage.getItem('ai_juku_session_token') || '';
      const headers = { 'Content-Type': 'application/json' };
      if (sessionToken) headers['Authorization'] = 'Bearer ' + sessionToken;
      const res = await fetch(`${BACKEND_URL}/api/mock-exam/generate`, {
        method: 'POST',
        headers: headers,
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
    const passage = q.passage ? `<div class="me-passage"><pre>${escapeHtmlBody(q.passage)}</pre></div>` : '';
    const audio = q.audio_script ? `<details class="me-audio-script"><summary>📢 音声スクリプト</summary><pre>${escapeHtmlBody(q.audio_script)}</pre></details>` : '';
    const prompt = q.prompt ? `<div class="me-prompt"><strong>${escapeHtmlBody(q.prompt)}</strong></div>` : '';
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
            <div class="me-subq-stem">${escapeHtmlBody(sq.stem)}</div>
            <div class="me-choices">${choices}</div>
          </div>
        `;
      } else {
        // 2026-05-10: essay 型は 5 AI 多視点採点 + 写真 upload 対応 (塾長指示「A+A」)
        // /api/mock-exam/grade-essay-multiview に POST → Claude Opus / GPT-4o / Sonnet / Gemini Pro / Haiku の
        // 5 視点で並列採点して accordion 表示
        const subqUid = `${q.exam_question_id}_${sq.id}`;
        const stemEscAttr = escapeHtml(sq.stem || '');  // data-* attribute 用 (素 escape)
        const stemEscBody = escapeHtmlBody(sq.stem || '');  // body 表示用 (<u> + 自動下線)
        const examLevel = (currentSession && currentSession.exam_type) || 'todai';
        return `
          <div class="me-subq me-subq-essay" data-uid="${subqUid}">
            <div class="me-subq-stem">${stemEscBody}</div>
            <textarea class="me-essay-input" id="meEssay_${subqUid}" rows="6"
                      placeholder="ここに英作文を入力 (or 下の📷ボタンで答案写真 upload)"></textarea>
            <div class="me-essay-actions">
              <label class="me-photo-label" for="mePhoto_${subqUid}">
                📷 写真でアップロード
                <input type="file" accept="image/*" capture="environment"
                       class="me-photo-input" id="mePhoto_${subqUid}"
                       data-uid="${subqUid}" style="display:none;">
              </label>
              <span class="me-photo-name" id="mePhotoName_${subqUid}"></span>
              <button class="me-grade-btn btn-primary" data-uid="${subqUid}"
                      data-stem="${stemEscAttr}" data-level="${escapeHtml(examLevel)}">
                🌟 5 AI 多視点で採点
              </button>
            </div>
            <div class="me-grade-result" id="meGradeResult_${subqUid}" style="display:none;"></div>
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
    // 2026-05-10: 写真 upload 対応 (5 AI 多視点採点)
    if (e.target.matches('.me-photo-input')) {
      onEssayPhotoChange(e);
    }
  }

  // 📷 写真 upload → base64 変換 + button にメタデータ保存
  function onEssayPhotoChange(e) {
    const file = e.target.files && e.target.files[0];
    const uid = e.target.dataset.uid;
    if (!file || !uid) return;
    if (file.size > 5 * 1024 * 1024) {
      alert('画像が大きすぎます (5MB 以内)');
      e.target.value = '';
      return;
    }
    const allowedMimes = ['image/jpeg', 'image/png', 'image/webp'];
    if (!allowedMimes.includes(file.type)) {
      alert('画像形式は JPEG / PNG / WebP のみ対応');
      e.target.value = '';
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      // data:image/...;base64,XXX → XXX 部分を抽出
      const dataUrl = reader.result || '';
      const b64 = dataUrl.split(',')[1] || '';
      const btn = document.querySelector(`.me-grade-btn[data-uid="${uid}"]`);
      if (btn) {
        btn.dataset.imageB64 = b64;
        btn.dataset.imageMime = file.type;
      }
      const nameEl = document.getElementById(`mePhotoName_${uid}`);
      if (nameEl) {
        nameEl.textContent = `📷 ${file.name} (${Math.round(file.size/1024)}KB)`;
        nameEl.style.color = '#86efac';
      }
    };
    reader.onerror = () => {
      alert('画像の読み込みに失敗しました');
      e.target.value = '';
    };
    reader.readAsDataURL(file);
  }

  // 🌟 5 AI 多視点採点 endpoint 呼出 + 結果描画
  async function onGradeEssayClick(e) {
    const btn = e.target.closest('.me-grade-btn');
    if (!btn) return;
    const uid = btn.dataset.uid;
    const stem = btn.dataset.stem || '';
    const level = btn.dataset.level || 'todai';
    const essay = (document.getElementById(`meEssay_${uid}`)?.value || '').trim();
    const imageB64 = btn.dataset.imageB64 || '';
    const imageMime = btn.dataset.imageMime || 'image/jpeg';

    if (!essay && !imageB64) {
      alert('テキスト入力 or 写真アップロードのいずれかが必要です');
      return;
    }
    if (essay && essay.length < 20 && !imageB64) {
      alert('英作文が短すぎます (20 文字以上 or 写真をアップロード)');
      return;
    }

    const studentId = parseInt(localStorage.getItem('aj_current_student_id') || '0', 10) || null;
    const orig = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '⏳ 5 AI が採点中... (60-90秒)';

    const resultDiv = document.getElementById(`meGradeResult_${uid}`);
    if (resultDiv) {
      resultDiv.style.display = 'block';
      resultDiv.innerHTML = `
        <div class="me-grade-loading">
          <div>🌟 5 AI が並列で採点中...</div>
          <div style="font-size:0.78rem;color:#94a3b8;margin-top:0.4rem;">
            🏗️ 構造 (Opus 4.7) · 💡 内容 (GPT-4o) · 📝 言語 (Sonnet) · 🎯 入試 (Gemini Pro) · 🌱 学習者目線 (Haiku)
          </div>
          <div class="me-grade-elapsed" style="font-size:0.85rem;color:#86efac;margin-top:0.6rem;font-weight:700;">
            経過 0 秒 (60-90 秒目安・固まったわけではありません)
          </div>
        </div>`;
    }
    // 経過秒タイマー (生徒の不安解消・3視点 review 反映 2026-05-10)
    const elapsedStart = Date.now();
    const elapsedTimer = setInterval(() => {
      const sec = Math.floor((Date.now() - elapsedStart) / 1000);
      const elapsedEl = resultDiv?.querySelector('.me-grade-elapsed');
      if (elapsedEl) {
        elapsedEl.textContent = `経過 ${sec} 秒 (60-90 秒目安・固まったわけではありません)`;
        if (sec > 90) elapsedEl.style.color = '#fbbf24';
      }
    }, 1000);

    try {
      const payload = {
        prompt: stem,
        level: level,
        student_id: studentId,
      };
      if (essay) payload.essay_text = essay;
      if (imageB64) {
        payload.image_base64 = imageB64;
        payload.mime_type = imageMime;
      }
      // 🛡️ IDOR fix 2026-05-26: session token あれば送る (backend で claims["student_id"] override)
      // → 攻撃者が他生徒の student_id を payload に入れて rate-limit 消費 / weakness 汚染防御
      const multiviewToken = localStorage.getItem('ai_juku_session_token') || '';
      const multiviewHeaders = { 'Content-Type': 'application/json' };
      if (multiviewToken) multiviewHeaders['Authorization'] = 'Bearer ' + multiviewToken;
      const res = await fetch(`${BACKEND_URL}/api/mock-exam/grade-essay-multiview`, {
        method: 'POST',
        headers: multiviewHeaders,
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok || !data.ok) {
        throw new Error(data.detail || `HTTP ${res.status}`);
      }
      if (typeof window.track === 'function') {
        window.track('mock_exam_grade_multiview', {
          successful_views: data.aggregate.successful_views,
          avg_total_30: data.aggregate.avg_total_30,
          with_image: !!imageB64,
        });
      }
      renderGradeResult(resultDiv, data);
    } catch (err) {
      if (resultDiv) {
        resultDiv.innerHTML = `<div class="me-grade-error">⚠️ 採点失敗: ${escapeHtml(err.message)}</div>`;
      }
    } finally {
      if (elapsedTimer) clearInterval(elapsedTimer);
    }
    btn.disabled = false;
    btn.innerHTML = orig;
  }

  // 5 AI 採点結果を accordion で描画
  function renderGradeResult(div, data) {
    if (!div) return;
    const agg = data.aggregate || {};
    const sa = agg.scores_avg || {};
    const total = agg.avg_total_30 != null ? agg.avg_total_30 : '--';
    const pct = agg.avg_pct != null ? agg.avg_pct : '--';

    const strengthsList = (agg.top_strengths || []).map(s => `<li>${escapeHtml(s)}</li>`).join('');
    const improvementsList = (agg.top_improvements || []).map(s => `<li>${escapeHtml(s)}</li>`).join('');

    const viewsHtml = (data.views || []).map(v => {
      if (v.error) {
        return `
          <details class="me-grade-view me-grade-view-error">
            <summary>${escapeHtml(v.label || v.view_id)} <span class="me-grade-error-badge">エラー</span> <span class="me-grade-view-model">${escapeHtml(v.model || '')}</span></summary>
            <div class="me-grade-view-comment">${escapeHtml(v.error)}</div>
          </details>`;
      }
      const t = v.total_30 != null ? v.total_30 : '--';
      const sc = v.scores || {};
      const strs = (v.strengths || []).map(escapeHtml).join('・');
      const imps = (v.improvements || []).map(escapeHtml).join('・');
      return `
        <details class="me-grade-view">
          <summary>
            ${escapeHtml(v.label || v.view_id)}
            <span class="me-grade-view-score">${t}/30</span>
            <span class="me-grade-view-model">${escapeHtml(v.model || '')}</span>
          </summary>
          <div class="me-grade-view-scores">
            構造 ${sc.structure ?? '--'} · 内容 ${sc.content ?? '--'} · 言語 ${sc.language ?? '--'}
          </div>
          <div class="me-grade-view-comment">${escapeHtml(v.comment_jp || '')}</div>
          ${strs ? `<div class="me-grade-view-strengths"><strong>💪 強み:</strong> ${strs}</div>` : ''}
          ${imps ? `<div class="me-grade-view-improvements"><strong>🎯 改善:</strong> ${imps}</div>` : ''}
        </details>`;
    }).join('');

    div.innerHTML = `
      <div class="me-grade-summary">
        <div class="me-grade-total-row">
          <span class="me-grade-total-num">${total}</span>
          <span class="me-grade-total-max">/30</span>
          <span class="me-grade-total-pct">${pct}%</span>
        </div>
        <div class="me-grade-stats">
          構造 ${sa.structure ?? '--'} · 内容 ${sa.content ?? '--'} · 言語 ${sa.language ?? '--'}
        </div>
        <div class="me-grade-meta">
          ${agg.successful_views || 0}/${agg.total_views || 5} AI 成功 · 所要 ${((data.elapsed_ms_total || 0) / 1000).toFixed(1)}秒
        </div>
      </div>
      ${strengthsList ? `<details class="me-grade-strengths" open>
        <summary>💪 強み (${(agg.top_strengths || []).length})</summary>
        <ul>${strengthsList}</ul>
      </details>` : ''}
      ${improvementsList ? `<details class="me-grade-improvements" open>
        <summary>🎯 改善点 (${(agg.top_improvements || []).length})</summary>
        <ul>${improvementsList}</ul>
      </details>` : ''}
      <h4 class="me-grade-views-title">各 AI の視点</h4>
      ${viewsHtml}
    `;
  }

  // 採点ボタン click を delegation で受ける (DOMContentLoaded 後の動的生成にも対応)
  document.addEventListener('click', (e) => {
    if (e.target.closest && e.target.closest('.me-grade-btn')) {
      onGradeEssayClick(e);
    }
  });

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
      // 🛡️ IDOR fix 2026-05-26: session token あれば送る (本人 session の改竄防御)
      // ゲスト session (student_id=NULL) は token 無しでも採点可
      const submitToken = localStorage.getItem('ai_juku_session_token') || '';
      const submitHeaders = { 'Content-Type': 'application/json' };
      if (submitToken) submitHeaders['Authorization'] = 'Bearer ' + submitToken;
      const res = await fetch(`${BACKEND_URL}/api/mock-exam/submit`, {
        method: 'POST',
        headers: submitHeaders,
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
    const shareText = `AIコーチングの完全模試で偏差値 ${data.deviation_estimate} (${data.percentage}%) でした! AI が動的に生成する模試で本番想定の演習ができます`;
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

  // 🎯 2026-05-22 塾長指示: 「下線部が引けていない」bug fix (HTML body 用)
  //   ① 問題データに <u>...</u> タグがあれば実 underline として復活 (whitelist 方式・XSS 安全)
  //   ② <u> 無し + 「下線部」を含む + (A)(B)(C)(D) 全揃いの正誤問題は自動で下線ラップ
  //   ※ HTML attribute (data-*) には escapeHtml を使うこと (この関数は <u> タグ出力するので attribute 用途では NG)
  const _UL_STYLE_ME = 'text-decoration:underline;text-decoration-thickness:2px;text-decoration-color:#6366f1;text-underline-offset:3px;background:linear-gradient(transparent 60%, rgba(99,102,241,0.18) 60%);padding:0 2px;';
  function escapeHtmlBody(s) {
    let out = escapeHtml(s);
    out = out
      .replace(/&lt;u&gt;/gi, `<u style="${_UL_STYLE_ME}">`)
      .replace(/&lt;\/u&gt;/gi, '</u>');
    const hasUTag = /<u[\s>]/i.test(out);
    const hasMarker = /下線部/.test(out) && /\(A\)[\s\S]*?\(B\)[\s\S]*?\(C\)[\s\S]*?\(D\)/.test(out);
    if (!hasUTag && hasMarker) {
      // nested 括弧対応: (A) the man (who is tired) (B) ... を破壊しない
      out = out.replace(
        /\(([A-D])\)\s*((?:[^(\n]|\([^)\n]*\))+?)(?=\s*\([A-D]\)|[.!?\n]|$)/g,
        (_m, letter, content) => `<u style="${_UL_STYLE_ME}">(${letter}) ${content.trim()}</u>`
      );
    }
    return out;
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
