/**
 * Learning Brain (学習の脳) — 個別最適化のコアエンジン
 *
 * 3つの差別化機能を提供:
 *  ① エビングハウス自動復習 (SM-2 アルゴリズム改変版)
 *  ② 適応的難易度 (per-student profile)
 *  ③ 躓きセンサー (連続不正解検知)
 *
 * すべて localStorage ベースで動作 (バックエンド不要・ログイン不要)
 * 将来的にバックエンド同期する場合は LB._sync() を実装
 */
(function () {
  'use strict';

  const STORAGE_PREFIX = 'ai_juku_lb__';

  // ==========================================================================
  // ストレージ層 (per-student キー)
  // ==========================================================================
  function _key(studentId, suffix) {
    return `${STORAGE_PREFIX}${studentId || 'guest'}__${suffix}`;
  }
  function _read(studentId, suffix, fallback) {
    try {
      const raw = localStorage.getItem(_key(studentId, suffix));
      return raw ? JSON.parse(raw) : (fallback ?? null);
    } catch { return fallback ?? null; }
  }
  function _write(studentId, suffix, value) {
    try { localStorage.setItem(_key(studentId, suffix), JSON.stringify(value)); }
    catch (e) { console.warn('LB storage write failed:', e); }
  }
  function _todayStr() {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
  }
  function _addDays(dateStr, days) {
    const d = new Date(dateStr);
    d.setDate(d.getDate() + days);
    return _formatDate(d);
  }
  function _formatDate(d) {
    return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
  }

  // ==========================================================================
  // ① SM-2 (Spaced Repetition) — エビングハウス忘却曲線対応
  // ==========================================================================
  // 各問題を以下のシリアル化された "card" として保存:
  //   { key, subject, topic, problem, answer, explanation,
  //     ease: 2.5, interval: 1, repetitions: 0, dueDate: 'YYYY-MM-DD',
  //     lapses: 0, history: [{date, correct, ease}] }
  //
  // SM-2: 正解(quality 4-5)→ interval拡大、不正解(quality<3)→ interval リセット

  function _initCard(opts) {
    return {
      key: opts.key,
      subject: opts.subject || 'その他',
      topic: opts.topic || '',
      problem: opts.problem || '',
      answer: opts.answer || '',
      explanation: opts.explanation || '',
      difficulty: opts.difficulty || '標準',
      ease: 2.5,
      interval: 0,  // 日数
      repetitions: 0,
      dueDate: _todayStr(),
      lapses: 0,
      history: [],
    };
  }

  function _scheduleNext(card, correct) {
    // 改変SM-2: シンプル化して使いやすく
    // 正解: 1日 → 3日 → 7日 → 21日 → 60日 (定着OKと判断したら止める)
    // 不正解: 翌日に再出題
    card.history.push({
      date: _todayStr(),
      correct,
      ease: card.ease,
    });
    if (correct) {
      card.repetitions += 1;
      // 段階的な間隔
      const intervals = [1, 3, 7, 21, 60];
      const idx = Math.min(card.repetitions - 1, intervals.length - 1);
      card.interval = intervals[idx];
      // ease を緩やかに上げる(easyだと早く間引く)
      card.ease = Math.min(3.0, card.ease + 0.1);
    } else {
      // 失敗 → 翌日に再挑戦、easeを下げる
      card.lapses += 1;
      card.repetitions = 0;
      card.interval = 1;
      card.ease = Math.max(1.3, card.ease - 0.2);
    }
    card.dueDate = _addDays(_todayStr(), card.interval);
    return card;
  }

  function recordAttempt(studentId, problemData, correct, opts) {
    if (!studentId) studentId = 'guest';
    const cards = _read(studentId, 'cards', {});
    const key = problemData.key || `${problemData.subject}__${problemData.problem}`.slice(0, 200);
    let card = cards[key];
    if (!card) {
      card = _initCard({
        key,
        subject: problemData.subject,
        topic: problemData.topic,
        problem: problemData.problem,
        answer: problemData.answer,
        explanation: problemData.explanation,
        difficulty: problemData.difficulty,
      });
    }
    _scheduleNext(card, correct);
    cards[key] = card;
    _write(studentId, 'cards', cards);

    // 適応難易度プロファイルも更新
    _updateProfile(studentId, problemData.subject, problemData.topic, correct, problemData.difficulty);

    return {
      nextDue: card.dueDate,
      interval: card.interval,
      lapses: card.lapses,
      reps: card.repetitions,
    };
  }

  function getDueReviews(studentId, limit = 50) {
    if (!studentId) studentId = 'guest';
    const cards = _read(studentId, 'cards', {});
    const today = _todayStr();
    const due = Object.values(cards)
      .filter(c => c.dueDate <= today)
      .sort((a, b) => {
        // 優先度: ① 既に苦戦中(lapses多) ② 古い ③ ease低い
        if (b.lapses !== a.lapses) return b.lapses - a.lapses;
        if (a.dueDate !== b.dueDate) return a.dueDate.localeCompare(b.dueDate);
        return a.ease - b.ease;
      })
      .slice(0, limit);
    return due;
  }

  function getReviewStats(studentId) {
    if (!studentId) studentId = 'guest';
    const cards = _read(studentId, 'cards', {});
    const today = _todayStr();
    const all = Object.values(cards);
    const due = all.filter(c => c.dueDate <= today).length;
    const total = all.length;
    const mastered = all.filter(c => c.repetitions >= 4).length;
    const struggling = all.filter(c => c.lapses >= 3).length;
    // 全体正答率
    let correct = 0, attempts = 0;
    all.forEach(c => {
      c.history.forEach(h => {
        attempts += 1;
        if (h.correct) correct += 1;
      });
    });
    const accuracy = attempts > 0 ? Math.round(correct / attempts * 100) : null;
    return { due, total, mastered, struggling, accuracy, attempts };
  }

  // ==========================================================================
  // ② 適応的難易度 (per-student profile)
  // ==========================================================================
  // profile = { '英語': { '関係代名詞': { correct, total, lastDifficulty } } }

  function _updateProfile(studentId, subject, topic, correct, difficulty) {
    const profile = _read(studentId, 'profile', {});
    profile[subject] = profile[subject] || {};
    const t = topic || '_general';
    profile[subject][t] = profile[subject][t] || { correct: 0, total: 0, lastDifficulty: '標準' };
    profile[subject][t].total += 1;
    if (correct) profile[subject][t].correct += 1;
    profile[subject][t].lastDifficulty = difficulty || '標準';
    profile[subject][t].lastAttempt = new Date().toISOString();
    _write(studentId, 'profile', profile);
  }

  /**
   * 次の出題に推奨する難易度を返す
   * - 直近10回の正答率で判断
   *   80%超 → 「応用」推奨
   *   50%未満 → 「基礎」推奨
   *   それ以外 → 「標準」
   */
  function recommendDifficulty(studentId, subject, topic) {
    if (!studentId) studentId = 'guest';
    const cards = _read(studentId, 'cards', {});
    const matches = Object.values(cards).filter(c =>
      c.subject === subject && (!topic || c.topic === topic || c.topic.includes(topic))
    );
    // 直近10回の正答率
    let correct = 0, attempts = 0;
    matches.forEach(c => {
      const recent = c.history.slice(-3);
      recent.forEach(h => {
        attempts += 1;
        if (h.correct) correct += 1;
      });
    });
    if (attempts < 5) return { difficulty: '標準', reason: 'データ不足', accuracy: null };
    const acc = correct / attempts;
    if (acc >= 0.8) return { difficulty: '応用', reason: `直近正答率${Math.round(acc*100)}%・難化推奨`, accuracy: Math.round(acc * 100) };
    if (acc < 0.5) return { difficulty: '基礎', reason: `直近正答率${Math.round(acc*100)}%・易化推奨`, accuracy: Math.round(acc * 100) };
    return { difficulty: '標準', reason: `直近正答率${Math.round(acc*100)}%`, accuracy: Math.round(acc * 100) };
  }

  // ==========================================================================
  // ③ 躓きセンサー (連続不正解検知)
  // ==========================================================================
  /**
   * 直近の同単元で 3 回以上不正解、または 4 回中 3 回以上不正解
   * → stumbling=true で警告対象
   */
  function detectStumbling(studentId, subject, topic) {
    if (!studentId) studentId = 'guest';
    const cards = _read(studentId, 'cards', {});
    const matches = Object.values(cards).filter(c =>
      c.subject === subject && (!topic || c.topic === topic || c.topic.includes(topic))
    );
    // 全 history を時系列に展開
    const all = [];
    matches.forEach(c => c.history.forEach(h => all.push({ ...h, key: c.key, problem: c.problem })));
    all.sort((a, b) => a.date.localeCompare(b.date));
    if (all.length < 3) return { stumbling: false, count: 0 };

    // 直近5回中の不正解
    const recent = all.slice(-5);
    const wrongCount = recent.filter(r => !r.correct).length;
    if (wrongCount >= 3) {
      return {
        stumbling: true,
        count: wrongCount,
        recentTotal: recent.length,
        message: `${subject}${topic ? `の${topic}` : ''}で直近${recent.length}回中${wrongCount}回不正解。基礎に戻って解説を熟読することを推奨します。`,
      };
    }
    return { stumbling: false, count: wrongCount };
  }

  function detectAllStumbling(studentId) {
    if (!studentId) studentId = 'guest';
    const profile = _read(studentId, 'profile', {});
    const alerts = [];
    Object.keys(profile).forEach(subject => {
      Object.keys(profile[subject]).forEach(topic => {
        const r = detectStumbling(studentId, subject, topic === '_general' ? '' : topic);
        if (r.stumbling) {
          alerts.push({
            subject,
            topic: topic === '_general' ? null : topic,
            ...r,
          });
        }
      });
    });
    return alerts;
  }

  // ==========================================================================
  // UI: 「今日の復習」レンダラー (mypage に埋め込む想定)
  // ==========================================================================
  function renderTodayReview(containerId, studentId) {
    const el = document.getElementById(containerId);
    if (!el) return;
    if (!studentId) studentId = 'guest';

    const due = getDueReviews(studentId, 100);
    const stats = getReviewStats(studentId);

    if (stats.total === 0) {
      el.innerHTML = `
        <div class="lb-empty">
          <p style="color: #94a3b8;">📋 復習カードがまだありません。</p>
          <p style="font-size: 0.85rem; color: #71717a;">問題を解いて「✓正解」「✗不正解」を記録すると、AIが自動的に復習タイミングを最適化します（エビングハウスの忘却曲線対応）。</p>
        </div>`;
      return;
    }

    const stumbling = detectAllStumbling(studentId);
    const stumblingHtml = stumbling.length > 0
      ? `<div class="lb-stumbling-alert" style="background: rgba(248,113,113,0.1); border: 1px solid rgba(248,113,113,0.3); border-radius: 10px; padding: 0.85rem; margin-bottom: 1rem;">
          <div style="font-weight: 800; color: #fca5a5; margin-bottom: 0.4rem;">⚠️ 躓きセンサー検知 (${stumbling.length}件)</div>
          ${stumbling.map(s => `<div style="font-size: 0.85rem; color: #fde68a; margin: 0.2rem 0;">• ${s.subject}${s.topic ? ` > ${s.topic}` : ''}: 直近${s.recentTotal}回中${s.count}回不正解</div>`).join('')}
          <div style="font-size: 0.78rem; color: #cbd5e1; margin-top: 0.5rem;">→ AIチューターで該当単元の解説を聞くか、基礎レベルから再挑戦しましょう。</div>
        </div>`
      : '';

    const dueHtml = due.length === 0
      ? `<div style="color: #34d399; padding: 1rem; text-align: center;">✅ 今日の復習は完了しました！</div>`
      : `<div class="lb-due-list">
          ${due.slice(0, 10).map(c => {
            const overdue = c.dueDate < _todayStr();
            return `
            <div class="lb-card" style="background: rgba(255,255,255,0.04); border: 1px solid ${overdue ? 'rgba(239,68,68,0.3)' : 'rgba(255,255,255,0.1)'}; border-radius: 10px; padding: 0.85rem; margin: 0.5rem 0;">
              <div style="display: flex; justify-content: space-between; align-items: start; gap: 0.5rem;">
                <div style="flex: 1; min-width: 0;">
                  <div style="font-size: 0.7rem; color: #818cf8; font-weight: 700;">${c.subject}${c.topic ? ` > ${c.topic}` : ''}${overdue ? ' ⚠️ 遅延' : ''}</div>
                  <div style="font-size: 0.92rem; color: #e4e4e7; margin: 0.3rem 0; line-height: 1.5;">${(c.problem || '').slice(0, 100)}${c.problem.length > 100 ? '...' : ''}</div>
                  <div style="font-size: 0.72rem; color: #71717a;">復習${c.repetitions}回 / 次回間隔${c.interval}日 / lapses${c.lapses}</div>
                </div>
                <div style="display: flex; flex-direction: column; gap: 0.4rem; flex-shrink: 0;">
                  <button onclick="LB.markCard('${c.key}', true, '${studentId}')" style="background: #10b981; color: white; border: none; padding: 0.4rem 0.8rem; border-radius: 6px; font-weight: 700; cursor: pointer; font-size: 0.8rem;">✓ 正解</button>
                  <button onclick="LB.markCard('${c.key}', false, '${studentId}')" style="background: #ef4444; color: white; border: none; padding: 0.4rem 0.8rem; border-radius: 6px; font-weight: 700; cursor: pointer; font-size: 0.8rem;">✗ 不正解</button>
                </div>
              </div>
              ${c.answer ? `<details style="margin-top: 0.5rem; font-size: 0.82rem;"><summary style="cursor: pointer; color: #a78bfa;">📖 解答を見る</summary><div style="padding: 0.5rem; background: rgba(0,0,0,0.3); border-radius: 6px; margin-top: 0.3rem; color: #cbd5e1;">${(c.answer || '').slice(0, 300)}${c.explanation ? `<br><br><strong>解説:</strong> ${(c.explanation || '').slice(0, 500)}` : ''}</div></details>` : ''}
            </div>`;
          }).join('')}
        </div>`;

    el.innerHTML = `
      <div class="lb-header" style="margin-bottom: 1rem;">
        <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
          <div style="background: rgba(99,102,241,0.15); padding: 0.5rem 0.9rem; border-radius: 8px; font-size: 0.85rem;"><strong style="color: #818cf8;">復習待ち</strong> ${stats.due}件</div>
          <div style="background: rgba(255,255,255,0.05); padding: 0.5rem 0.9rem; border-radius: 8px; font-size: 0.85rem;">登録カード ${stats.total}件</div>
          <div style="background: rgba(16,185,129,0.1); padding: 0.5rem 0.9rem; border-radius: 8px; font-size: 0.85rem;"><strong style="color: #6ee7b7;">定着済</strong> ${stats.mastered}件</div>
          ${stats.accuracy !== null ? `<div style="background: rgba(99,102,241,0.08); padding: 0.5rem 0.9rem; border-radius: 8px; font-size: 0.85rem;">総合正答率 ${stats.accuracy}%</div>` : ''}
        </div>
      </div>
      ${stumblingHtml}
      ${dueHtml}
    `;
  }

  /**
   * カードを正解/不正解でマーク (UIから呼出)
   */
  function markCard(key, correct, studentId) {
    if (!studentId) studentId = 'guest';
    const cards = _read(studentId, 'cards', {});
    const card = cards[key];
    if (!card) { alert('カードが見つかりません'); return; }
    _scheduleNext(card, correct);
    cards[key] = card;
    _write(studentId, 'cards', cards);
    // 同タブの「今日の復習」を再描画
    const containers = ['lbTodayReview', 'lbReviewWidget'];
    containers.forEach(id => {
      if (document.getElementById(id)) renderTodayReview(id, studentId);
    });
  }

  // ==========================================================================
  // 既存の "問題セット" を Learning Brain に流し込むヘルパー
  // ==========================================================================
  function importProblemsAsCards(studentId, subject, topic, problems, difficulty) {
    if (!studentId) studentId = 'guest';
    if (!Array.isArray(problems)) return 0;
    const cards = _read(studentId, 'cards', {});
    let added = 0;
    problems.forEach(p => {
      const key = `${subject}__${(p.question || p.problem || '').slice(0, 100)}`;
      if (cards[key]) return;  // 既存スキップ
      cards[key] = _initCard({
        key,
        subject,
        topic: topic || '',
        problem: p.question || p.problem || '',
        answer: p.answer || '',
        explanation: p.explanation || '',
        difficulty: difficulty || '標準',
      });
      added += 1;
    });
    _write(studentId, 'cards', cards);
    return added;
  }

  // ==========================================================================
  // 公開 API
  // ==========================================================================
  window.LB = {
    recordAttempt,
    getDueReviews,
    getReviewStats,
    recommendDifficulty,
    detectStumbling,
    detectAllStumbling,
    renderTodayReview,
    markCard,
    importProblemsAsCards,
    // テスト用
    _read, _write, _todayStr,
  };
})();
