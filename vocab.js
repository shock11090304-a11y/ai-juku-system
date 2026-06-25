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
  let mistakesOnly = false; // 🔴 mistakes-only モード (塾長指示 2026-05-25)
  let mistakesListLoaded = false;

  // === HTML escape (XSS 防止) ===
  function esc(s) {
    if (s == null) return '';
    return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }

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

  // 🔑 2026-06-14 [trust-identity] 現在の生徒は「サーバ検証済みのログイン本人」(AuthGuard)を
  //   権威ソースにする。従来は aj_current_student_id 未設定時にハードコード 1 へ落ち、別生徒
  //   (id=1) の単語統計を表示し採点を id=1 に書き込む二重事故があった。ハードコード 1 は撤去。
  function getStudentId() {
    try {
      const s = (window.AuthGuard && window.AuthGuard.getStudent) ? window.AuthGuard.getStudent() : null;
      if (s && s.id != null) return s.id;
    } catch (e) {}
    const id = localStorage.getItem('aj_current_student_id');
    return id ? parseInt(id) : null; // 本人不明: backend が Bearer token から本人 id を強制解決する
  }

  // 認証付き fetch (Authorization: Bearer を自動付与)。backend はこの token から本人 id を
  //   解決し、URL の student_id がずれていても他生徒データを返さない/汚染させない。
  function vfetch(url, init) {
    if (window.AuthGuard && window.AuthGuard.authFetch) return window.AuthGuard.authFetch(url, init);
    return fetch(url, init); // auth-guard 未読込時の後方互換 (通常は起きない)
  }

  // === 統計取得 ===
  async function loadStats() {
    try {
      const studentId = getStudentId();
      const res = await vfetch(`${BACKEND_URL}/api/vocab/stats?student_id=${studentId}`);
      if (!res.ok) return;
      const s = await res.json();
      document.getElementById('vcStatsCard').style.display = '';
      document.getElementById('vcDueNow').textContent = s.due_now || 0;
      document.getElementById('vcMastered').textContent = s.mastered || 0;
      document.getElementById('vcAccuracy').textContent = (s.accuracy_percent || 0) + '%';
      document.getElementById('vcTotal').textContent = s.total_words_in_pool || 0;
      const mc = s.mistakes_count || 0;
      const mEl = document.getElementById('vcMistakes');
      if (mEl) mEl.textContent = mc;
      // 🔴 間違えた単語タグ panel の表示制御
      const panel = document.getElementById('vcMistakesPanel');
      const countBig = document.getElementById('vcMistakesCountBig');
      const listEl = document.getElementById('vcMistakesList');
      const listBtn = document.getElementById('vcMistakeListToggleBtn');
      if (panel) {
        if (mc > 0) {
          panel.style.display = '';
          if (countBig) countBig.textContent = mc + ' 件';
        } else {
          // 0 件になったら panel 自体を隠す + 一覧/ボタンの状態も初期化
          panel.style.display = 'none';
          if (listEl) listEl.style.display = 'none';
          if (listBtn) listBtn.textContent = '📋 一覧を見る';
        }
      }
      // 統計が更新されたら一覧 cache を無効化
      mistakesListLoaded = false;
      if (listEl && listEl.style.display !== 'none' && panel && panel.style.display !== 'none') {
        await renderMistakesList();
      }
    } catch (e) {
      console.warn('stats load failed', e);
    }
  }

  // === 🔴 間違えた単語一覧取得 + 描画 ===
  async function renderMistakesList() {
    const listEl = document.getElementById('vcMistakesList');
    if (!listEl) return;
    listEl.innerHTML = '<div class="vc-mistakes-list-loading">読み込み中…</div>';
    try {
      const studentId = getStudentId();
      const params = new URLSearchParams({ student_id: studentId, limit: 100 });
      if (currentLevel) params.set('level', currentLevel);
      if (currentUniv) params.set('univ', currentUniv);
      const res = await vfetch(`${BACKEND_URL}/api/vocab/mistaken-words?${params}`);
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const data = await res.json();
      const items = data.items || [];
      if (items.length === 0) {
        listEl.innerHTML = '<div class="vc-mistakes-list-empty">該当する間違えた単語はありません。レベル/大学フィルタを外すと表示されるかもしれません。</div>';
        mistakesListLoaded = true;
        return;
      }
      const rows = items.map(it => {
        const posLabel = it.pos_label_jp ? `<span class="vc-mistake-pos">${esc(it.pos_label_jp)}</span>` : '';
        const acc = (it.accuracy_percent != null) ? `${it.accuracy_percent}%` : '--';
        return `
          <div class="vc-mistake-row">
            <div class="vc-mistake-word-block">
              <div class="vc-mistake-word">${esc(it.word)}</div>
              <div class="vc-mistake-meta">${posLabel}<span class="vc-mistake-level">${esc(it.level || '')}</span></div>
            </div>
            <div class="vc-mistake-meaning">${esc(it.meaning_jp || '')}</div>
            <div class="vc-mistake-stats">
              <span class="vc-mistake-count-badge" title="誤答回数">❌ ${esc(it.mistake_count)}</span>
              <span class="vc-mistake-acc" title="正答率">正答 ${esc(acc)}</span>
            </div>
          </div>`;
      }).join('');
      listEl.innerHTML = `<div class="vc-mistakes-list-inner">${rows}</div>`;
      mistakesListLoaded = true;
    } catch (e) {
      listEl.innerHTML = `<div class="vc-mistakes-list-empty">一覧取得失敗: ${esc(e.message)}</div>`;
    }
  }

  // === キュー取得 (4 択クイズ endpoint) ===
  async function loadQueue(level, univ, useMistakesOnly) {
    const studentId = getStudentId();
    const fetchLimit = univ ? 60 : 20;
    const params = new URLSearchParams({ student_id: studentId, limit: fetchLimit });
    if (level) params.set('level', level);
    if (univ) params.set('univ', univ);
    if (useMistakesOnly) params.set('mistakes_only', '1');
    try {
      const res = await vfetch(`${BACKEND_URL}/api/vocab/quiz?${params}`);
      if (!res.ok) throw new Error(`Quiz fetch failed: ${res.status}`);
      const data = await res.json();
      queue = (data.quiz || []).slice(0, 20);
      queueIndex = 0;
      reviewedCount = 0;
      correctCount = 0;
      currentLevel = level;
      currentUniv = univ;
      mistakesOnly = !!useMistakesOnly;
      if (queue.length === 0) {
        let msg;
        if (useMistakesOnly) {
          msg = '🎉 該当する間違えた単語はありません。レベル/大学フィルタを外して再試行するか、通常クイズを進めてください。';
        } else if (univ) {
          msg = `${univ.toUpperCase()} 頻出単語の在庫がまだ少ないです。別大学/全レベルでお試しください。`;
        } else {
          msg = '現在復習対象の単語がありません。別レベルを選ぶか、新規単語の追加をお待ちください。';
        }
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

    // grade を SRS バックエンドに送信 → 返却の次回復習日を画面に表示
    const studentId = getStudentId();
    const nextReviewEl = document.getElementById('vcNextReview');
    if (nextReviewEl) { nextReviewEl.style.display = 'none'; nextReviewEl.textContent = ''; }
    vfetch(`${BACKEND_URL}/api/vocab/grade`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ student_id: studentId, word_id: w.id, knew: isCorrect }),
    })
      .then(res => res.ok ? res.json() : null)
      .then(data => {
        if (!data || !nextReviewEl) return;
        const days = data.next_review_in_days;
        if (days == null) return;
        // FSRS なら 🧠、Leitner なら 📦。「次回復習: ◯日後」を表示。
        const isFsrs = data.scheduler === 'fsrs';
        const icon = isFsrs ? '🧠' : '📦';
        const whenTxt = days >= 1 ? `${days}日後` : '今日中';
        let txt = `${icon} 次回復習: ${whenTxt}`;
        if (isFsrs && typeof data.stability === 'number') {
          // 定着度(安定度) を補足表示。日数=記憶がR=90%まで保つ目安。
          txt += `（定着度 ${Math.round(data.stability)}日）`;
        }
        nextReviewEl.textContent = txt;
        nextReviewEl.style.display = '';
      })
      .catch(e => console.warn('grade failed', e));

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
    const ok = await loadQueue(currentLevel, currentUniv, false);
    if (!ok) return;
    document.getElementById('vcSetup').style.display = 'none';
    document.getElementById('vcReview').style.display = 'block';
    document.getElementById('vcComplete').style.display = 'none';
    if (typeof window.track === 'function') window.track('vocab_session_start', { level: currentLevel, mode: 'quiz4' });
    renderCard();
  }

  // === 🔴 間違えた単語だけのクイズ開始 ===
  async function startMistakeReview() {
    const ok = await loadQueue(currentLevel, currentUniv, true);
    if (!ok) return;
    document.getElementById('vcSetup').style.display = 'none';
    document.getElementById('vcReview').style.display = 'block';
    document.getElementById('vcComplete').style.display = 'none';
    if (typeof window.track === 'function') window.track('vocab_session_start', { level: currentLevel, mode: 'mistakes_only' });
    renderCard();
  }

  document.addEventListener('DOMContentLoaded', () => {
    loadStats();

    // フィルタ変更時は mistakes 一覧 cache を無効化し、開いていれば再描画
    async function invalidateMistakesListOnFilterChange() {
      mistakesListLoaded = false;
      const listEl = document.getElementById('vcMistakesList');
      const panel = document.getElementById('vcMistakesPanel');
      if (listEl && listEl.style.display !== 'none' && panel && panel.style.display !== 'none') {
        await renderMistakesList();
      }
    }

    document.querySelectorAll('.vc-level-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.vc-level-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentLevel = btn.dataset.level || '';
        invalidateMistakesListOnFilterChange();
      });
    });
    const defaultLevelBtn = document.querySelector('.vc-level-btn[data-level=""]');
    if (defaultLevelBtn) defaultLevelBtn.classList.add('active');

    document.querySelectorAll('.vc-univ-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.vc-univ-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentUniv = btn.dataset.univ || '';
        invalidateMistakesListOnFilterChange();
      });
    });

    document.getElementById('vcStartBtn').addEventListener('click', startReview);

    // 🔴 間違えた単語タグ panel buttons
    const mistakeBtn = document.getElementById('vcMistakeReviewBtn');
    if (mistakeBtn) mistakeBtn.addEventListener('click', startMistakeReview);
    const mistakeListBtn = document.getElementById('vcMistakeListToggleBtn');
    if (mistakeListBtn) {
      mistakeListBtn.addEventListener('click', async () => {
        const listEl = document.getElementById('vcMistakesList');
        if (!listEl) return;
        const isHidden = listEl.style.display === 'none';
        if (isHidden) {
          listEl.style.display = '';
          mistakeListBtn.textContent = '📋 一覧を閉じる';
          if (!mistakesListLoaded) await renderMistakesList();
        } else {
          listEl.style.display = 'none';
          mistakeListBtn.textContent = '📋 一覧を見る';
        }
      });
    }

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
