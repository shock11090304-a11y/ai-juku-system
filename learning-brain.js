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
    const now = new Date();
    card.history.push({
      date: _todayStr(),
      hour: now.getHours(),
      dow: now.getDay(),  // 0=日 ... 6=土
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
  // ③ 学習時間帯最適化 (Best Hour Recommendation)
  // ==========================================================================
  // 過去の history.hour と history.correct から
  // 時間帯ごとの正答率を集計し、最適な学習時間を推奨。
  // 曜日別パターンも返す。
  function analyzeStudyTimes(studentId) {
    if (!studentId) studentId = 'guest';
    const cards = _read(studentId, 'cards', {});
    const all = [];
    Object.values(cards).forEach(c => {
      (c.history || []).forEach(h => {
        if (typeof h.hour === 'number') all.push(h);
      });
    });
    if (all.length === 0) {
      return { ready: false, reason: 'データ不足', samples: 0 };
    }

    // 時間帯バケット (0-5, 6-9, 10-12, 13-17, 18-21, 22-23)
    const buckets = [
      { key: 'dawn',     label: '深夜・早朝 (0-5時)',  range: [0, 5],   correct: 0, total: 0 },
      { key: 'morning',  label: '朝 (6-9時)',       range: [6, 9],   correct: 0, total: 0 },
      { key: 'noon',     label: '昼 (10-12時)',      range: [10, 12], correct: 0, total: 0 },
      { key: 'afternoon',label: '午後 (13-17時)',    range: [13, 17], correct: 0, total: 0 },
      { key: 'evening',  label: '夜 (18-21時)',      range: [18, 21], correct: 0, total: 0 },
      { key: 'night',    label: '深夜 (22-23時)',    range: [22, 23], correct: 0, total: 0 },
    ];
    all.forEach(h => {
      const b = buckets.find(b => h.hour >= b.range[0] && h.hour <= b.range[1]);
      if (!b) return;
      b.total += 1;
      if (h.correct) b.correct += 1;
    });
    buckets.forEach(b => {
      b.accuracy = b.total > 0 ? Math.round(b.correct / b.total * 100) : null;
    });

    // 最良時間帯 (サンプル数3以上の中で正答率最大)
    const valid = buckets.filter(b => b.total >= 3);
    let best = null;
    if (valid.length > 0) {
      best = valid.reduce((a, b) => (b.accuracy > a.accuracy ? b : a));
    }

    // 曜日別 (日=0 ... 土=6)
    const dowNames = ['日','月','火','水','木','金','土'];
    const dowStats = dowNames.map(n => ({ day: n, correct: 0, total: 0 }));
    all.forEach(h => {
      if (typeof h.dow === 'number' && h.dow >= 0 && h.dow <= 6) {
        dowStats[h.dow].total += 1;
        if (h.correct) dowStats[h.dow].correct += 1;
      }
    });
    dowStats.forEach(d => {
      d.accuracy = d.total > 0 ? Math.round(d.correct / d.total * 100) : null;
    });
    const validDow = dowStats.filter(d => d.total >= 3);
    const bestDow = validDow.length > 0
      ? validDow.reduce((a, b) => (b.accuracy > a.accuracy ? b : a))
      : null;

    return {
      ready: true,
      samples: all.length,
      buckets,
      best,
      dowStats,
      bestDow,
    };
  }

  function recommendStudyTime(studentId) {
    const r = analyzeStudyTimes(studentId);
    if (!r.ready || !r.best) {
      return {
        ready: false,
        message: '学習データが不足しています。問題を10問以上解くと、最適な学習時間帯を AI が分析します。',
      };
    }
    const parts = [`📊 あなたの最適学習時間帯は ${r.best.label} (正答率 ${r.best.accuracy}%, ${r.best.total}問)`];
    if (r.bestDow && r.bestDow.accuracy >= 70) {
      parts.push(`🗓 集中しやすい曜日: ${r.bestDow.day}曜 (正答率 ${r.bestDow.accuracy}%)`);
    }
    return { ready: true, message: parts.join('\n'), best: r.best, bestDow: r.bestDow, buckets: r.buckets, dowStats: r.dowStats };
  }

  function renderStudyTimeWidget(containerId, studentId) {
    const el = document.getElementById(containerId);
    if (!el) return;
    if (!studentId) studentId = 'guest';
    const r = analyzeStudyTimes(studentId);
    if (!r.ready) {
      el.innerHTML = `<div style="color:#94a3b8;padding:0.8rem;font-size:0.9rem;">📊 学習時間帯分析: データを蓄積中。問題を10問以上解くと、AI が最適な学習時間帯を分析します。</div>`;
      return;
    }
    const maxAcc = Math.max(...r.buckets.filter(b => b.accuracy !== null).map(b => b.accuracy));
    const barsHtml = r.buckets.map(b => {
      if (b.total === 0) {
        return `<div style="display:flex;align-items:center;gap:0.5rem;margin:0.25rem 0;font-size:0.8rem;"><div style="width:140px;color:#71717a;">${b.label}</div><div style="flex:1;color:#52525b;">未学習</div></div>`;
      }
      const isBest = r.best && b.key === r.best.key;
      const widthPct = b.accuracy;
      const color = isBest ? 'linear-gradient(90deg,#10b981,#34d399)' : 'rgba(99,102,241,0.4)';
      return `<div style="display:flex;align-items:center;gap:0.5rem;margin:0.25rem 0;font-size:0.8rem;">
        <div style="width:140px;color:${isBest ? '#34d399' : '#cbd5e1'};font-weight:${isBest ? 700 : 400};">${b.label}${isBest ? ' ⭐' : ''}</div>
        <div style="flex:1;background:rgba(255,255,255,0.05);border-radius:4px;height:18px;position:relative;">
          <div style="background:${color};width:${widthPct}%;height:100%;border-radius:4px;"></div>
          <div style="position:absolute;top:0;left:0.4rem;line-height:18px;font-weight:700;color:#e4e4e7;font-size:0.75rem;">${b.accuracy}% (${b.total}問)</div>
        </div>
      </div>`;
    }).join('');

    const dowHtml = r.bestDow
      ? `<div style="margin-top:0.6rem;padding:0.5rem;background:rgba(16,185,129,0.08);border-radius:8px;font-size:0.82rem;color:#a7f3d0;">🗓 最も集中できている曜日: <strong>${r.bestDow.day}曜</strong> (正答率 ${r.bestDow.accuracy}%, ${r.bestDow.total}問)</div>`
      : '';

    el.innerHTML = `
      <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:0.85rem;">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.5rem;">
          <div style="font-weight:800;color:#a78bfa;">⏰ 学習時間帯分析 (${r.samples}件)</div>
          ${r.best ? `<div style="font-size:0.78rem;color:#34d399;">⭐ 最適: ${r.best.label.split(' ')[0]}</div>` : ''}
        </div>
        ${barsHtml}
        ${dowHtml}
      </div>`;
  }

  // ==========================================================================
  // ⑤ 躓きセンサー (連続不正解検知)
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
  // 🧮 KaTeX 自動組版 (CDN defer load 対応で未ロード時はリトライ・app.js/english-exam.js と同方式)。
  //   delimiters は $$ / \[ / \( のみ (単一 $ は英語カードの通貨 $ 誤組版を避けるため除外。理系カードは \( 使用)。
  function _lbApplyKatex(rootEl) {
    if (!rootEl) return;
    const run = () => {
      if (typeof window.renderMathInElement !== 'function') return false;
      try {
        // 🔢 2026-07-14: 区切り忘れの生数式(不等号≥≦≠・裸\geq\dfrac)を \(..\) 化して描画に載せる (math-wrap.js)
        if (typeof window.wrapBareMath === 'function') window.wrapBareMath(rootEl);
        window.renderMathInElement(rootEl, {
          delimiters: [
            { left: '$$', right: '$$', display: true },
            { left: '\\[', right: '\\]', display: true },
            { left: '\\(', right: '\\)', display: false },
          ],
          throwOnError: false,
          errorColor: '#f87171',
          strict: 'ignore',
        });
      } catch (e) { console.warn('[LB katex] render failed', e); }
      return true;
    };
    if (run()) return;
    let tries = 0;
    const id = setInterval(() => { tries++; if (run() || tries > 20) clearInterval(id); }, 200);
  }

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

    // ✅ 2026-05-22 致命 fix: onclick 文字列補間で問題文 (apostrophe/quote 含む) を生埋め込みすると
    // JS が壊れて全カードのボタンが silent fail。data-* + addEventListener + escapeHtml に置換。
    // 🎯 2026-05-22 塾長指示: 「下線部が引けていない」bug fix
    //   ① 問題データに <u>...</u> タグがあれば実 underline として復活 (whitelist 方式・XSS 安全)
    //   ② <u> 無し + 「下線部」を含む + (A)(B)(C)(D) 全揃いの正誤問題は自動で下線ラップ
    //   english-exam.js の escapeTextWithMath パターン準拠
    const _UL_STYLE = 'text-decoration:underline;text-decoration-thickness:2px;text-decoration-color:#a78bfa;text-underline-offset:3px;background:linear-gradient(transparent 60%, rgba(167,139,250,0.20) 60%);padding:0 2px;';
    const _escHtml = (s) => {
      if (s == null) return '';
      let out = String(s).replace(/[&<>"']/g, ch =>
        ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[ch]);
      // ① <u>...</u> whitelist 復活 (他タグは escape 維持で XSS 安全)
      out = out
        .replace(/&lt;u&gt;/gi, `<u style="${_UL_STYLE}">`)
        .replace(/&lt;\/u&gt;/gi, '</u>');
      // ② 「下線部」かつ (A)(B)(C)(D) 全揃いかつ既存 <u> 無しの場合のみ自動ラップ
      //   (TOEIC 写真説明等の (A)(B)(C)(D) 選択肢には「下線部」が無いので発火しない)
      const hasUTag = /<u[\s>]/i.test(out);
      const hasMarker = /下線部/.test(out) && /\(A\)[\s\S]*?\(B\)[\s\S]*?\(C\)[\s\S]*?\(D\)/.test(out);
      if (!hasUTag && hasMarker) {
        // nested 括弧対応: (A) the man (who is tired) (B) ... のような関係詞節を破壊しない
        // `(?:[^(\n]|\([^)\n]*\))+?` = 「( でない文字」 or 「(...) 括弧 (改行と ) を含まない単純括弧)」
        out = out.replace(
          /\(([A-D])\)\s*((?:[^(\n]|\([^)\n]*\))+?)(?=\s*\([A-D]\)|[.!?\n]|$)/g,
          (_m, letter, content) => `<u style="${_UL_STYLE}">(${letter}) ${content.trim()}</u>`
        );
      }
      return out;
    };
    const _escAttr = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, ch =>
      ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[ch]);
    // ✅ 2026-05-22 塾長指示: 選択肢 (A)(B)(C)(D) パターンを解析して click 自動採点 UI を有効化
    // 問題文に (A) ... (B) ... 等のパターンがあれば main stem + 選択肢配列に分割
    const _parseChoices = (text) => {
      if (!text || typeof text !== 'string') return null;
      const re = /\(([A-Dア-エ1-4])\)\s*([\s\S]+?)(?=\(([A-Dア-エ1-4])\)|$)/g;
      const choices = [];
      let m;
      while ((m = re.exec(text)) !== null) {
        choices.push({ letter: m[1], text: m[2].replace(/\s+$/, '').trim() });
        if (choices.length >= 6) break;
      }
      if (choices.length < 2) return null;  // 最低 2 択以上で有効
      const firstIdx = text.indexOf('(' + choices[0].letter + ')');
      const stem = firstIdx > 0 ? text.slice(0, firstIdx).trim() : '';
      return { stem, choices };
    };
    // 正解選択肢を answer から抽出 (seed data の各種 format 対応)
    // choicesLetters: parseChoices.choices.map(c=>c.letter) で choice 側の letter list を渡すと
    // bare digit answer ("0"/"1"/"2") の zero-indexed vs one-indexed を choices と整合判定
    // e.g., choices=[1,2,3,4] + answer="2" → "2" (one-indexed) / choices=[A,B,C,D] + answer="2" → "C"
    const _extractCorrectLetter = (answer, choicesLetters) => {
      // 整数防御: String 化 + trim 後に空文字なら null
      const text = String(answer == null ? '' : answer).trim();
      if (!text) return null;
      // 1) (X) パターン (最優先・確実)
      const m1 = text.match(/\(([A-Dア-エ])\)/);
      if (m1) return m1[1];
      // 2) "正解: X" / "答え: X" / "回答: X" / "答え X" 系 (半角/全角コロン両対応)
      const m2 = text.match(/(?:正解|答え|回答|解答|答)[::\s\t]*\s*\(?([A-Dア-エ])\)?/);
      if (m2) return m2[1];
      // 3) 文頭の単独文字 (X / X. / X、 / X」 等)
      const m3 = text.match(/^[\s「『]*([A-Dア-エ])(?:[\s.。、」』:：]|$)/);
      if (m3) return m3[1];
      // 4) bare digit answer: choicesLetters に [1-4] が含まれれば one-indexed そのまま返却
      //    含まれていなければ zero-indexed → A/B/C/D 変換 (backend seed format)
      const isOneIndexedChoices = Array.isArray(choicesLetters)
        && choicesLetters.some(l => /^[1-4]$/.test(String(l)));
      if (/^[0-3]$/.test(text)) {
        if (isOneIndexedChoices && /^[1-3]$/.test(text)) return text;  // one-indexed digit choices
        return ['A', 'B', 'C', 'D'][parseInt(text, 10)];  // zero-indexed (default)
      }
      // 5) "正解: 0" 系も同様
      const m5 = text.match(/(?:正解|答え|回答|解答|答)[::\s\t]*\s*([0-3])(?:\b|$)/);
      if (m5) {
        const dig = m5[1];
        if (isOneIndexedChoices && /^[1-3]$/.test(dig)) return dig;
        return ['A', 'B', 'C', 'D'][parseInt(dig, 10)];
      }
      // 6) "4" 単独 → one-indexed の 4 として返す ("4" は zero-indexed 範囲外)
      if (/^4$/.test(text)) return '4';
      return null;
    };
    const dueHtml = due.length === 0
      ? `<div style="color: #34d399; padding: 1rem; text-align: center;">✅ 今日の復習は完了しました！</div>`
      : `<div class="lb-due-list">
          ${due.slice(0, 10).map(c => {
            const overdue = c.dueDate < _todayStr();
            // ✅ 2026-05-22 塾長指示: 問題文が 100 字超過時は details で「全文を見る」展開
            const probShort = (c.problem || '').slice(0, 100);
            const probIsLong = c.problem && c.problem.length > 100;
            const probFullHtml = probIsLong
              ? `${_escHtml(probShort)}<details style="display:inline; margin-left:0.3rem;"><summary style="cursor:pointer; color:#a78bfa; display:inline; font-size:0.82rem;">… 全文を見る</summary><div style="margin-top:0.4rem; padding:0.6rem; background:rgba(0,0,0,0.30); border:1px solid rgba(167,139,250,0.20); border-radius:6px; color:#e4e4e7; white-space:pre-wrap; line-height:1.6; max-height:300px; overflow-y:auto;">${_escHtml(c.problem)}</div></details>`
              : _escHtml(probShort);
            // 解答・解説も同様に全文展開可能に
            const ansShort = (c.answer || '').slice(0, 300);
            const ansIsLong = c.answer && c.answer.length > 300;
            const explShort = (c.explanation || '').slice(0, 500);
            const explIsLong = c.explanation && c.explanation.length > 500;
            const ansHtml = ansIsLong
              ? `${_escHtml(ansShort)}<details style="display:inline; margin-left:0.3rem;"><summary style="cursor:pointer; color:#a78bfa; display:inline; font-size:0.78rem;">… 全文を見る</summary><div style="margin-top:0.3rem; padding:0.5rem; background:rgba(0,0,0,0.25); border-radius:6px; white-space:pre-wrap; max-height:300px; overflow-y:auto;">${_escHtml(c.answer)}</div></details>`
              : _escHtml(ansShort);
            const explHtml = explIsLong
              ? `${_escHtml(explShort)}<details style="display:inline; margin-left:0.3rem;"><summary style="cursor:pointer; color:#a78bfa; display:inline; font-size:0.78rem;">… 全文を見る</summary><div style="margin-top:0.3rem; padding:0.5rem; background:rgba(0,0,0,0.25); border-radius:6px; white-space:pre-wrap; max-height:300px; overflow-y:auto;">${_escHtml(c.explanation)}</div></details>`
              : _escHtml(explShort);
            // ✅ 2026-05-22 塾長指示: 選択肢自動採点 UI (問題文に (A)(B)(C)(D) パターンがあれば有効化)
            const parsed = _parseChoices(c.problem);
            const hasInteractive = parsed && parsed.choices && parsed.choices.length >= 2;
            // ✅ 2026-05-22: choices の letter list を渡して one-indexed vs zero-indexed を文脈判定
            const correctLetter = hasInteractive
              ? _extractCorrectLetter(c.answer, parsed.choices.map(ch => ch.letter))
              : null;
            const interactiveHtml = hasInteractive ? `
              <details class="lb-interactive" data-key="${_escAttr(c.key)}" data-sid="${_escAttr(studentId)}" data-correct="${_escAttr(correctLetter || '')}" style="margin-top: 0.6rem; font-size: 0.85rem;">
                <summary style="cursor: pointer; color: #10b981; font-weight: 700; padding: 0.4rem 0.7rem; background: rgba(16,185,129,0.12); border: 1px solid rgba(16,185,129,0.35); border-radius: 8px;">📝 解いてみる (選択肢から選ぶ・自動採点)</summary>
                <div style="padding: 0.8rem; background: rgba(0,0,0,0.30); border: 1px solid rgba(16,185,129,0.25); border-radius: 8px; margin-top: 0.4rem;">
                  ${parsed.stem ? `<div style="margin-bottom: 0.7rem; white-space: pre-wrap; line-height: 1.6; color: #e4e4e7;">${_escHtml(parsed.stem)}</div>` : ''}
                  <div class="lb-choices" style="display: grid; gap: 0.4rem;">
                    ${parsed.choices.map(ch => `
                      <button type="button" class="lb-choice-btn" data-choice="${_escAttr(ch.letter)}" style="text-align: left; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.15); border-radius: 8px; padding: 0.55rem 0.85rem; color: #e4e4e7; font-size: 0.88rem; cursor: pointer; line-height: 1.5;">(${_escHtml(ch.letter)}) ${_escHtml(ch.text)}</button>
                    `).join('')}
                  </div>
                  <div class="lb-feedback" style="display: none; margin-top: 0.6rem; padding: 0.5rem 0.7rem; border-radius: 8px; font-weight: 700; font-size: 0.92rem;"></div>
                </div>
              </details>
            ` : '';
            return `
            <div class="lb-card" style="background: rgba(255,255,255,0.04); border: 1px solid ${overdue ? 'rgba(239,68,68,0.3)' : 'rgba(255,255,255,0.1)'}; border-radius: 10px; padding: 0.85rem; margin: 0.5rem 0;">
              <div style="display: flex; justify-content: space-between; align-items: start; gap: 0.5rem;">
                <div style="flex: 1; min-width: 0;">
                  <div style="font-size: 0.7rem; color: #818cf8; font-weight: 700;">${_escHtml(c.subject)}${c.topic ? ` > ${_escHtml(c.topic)}` : ''}${overdue ? ' ⚠️ 遅延' : ''}</div>
                  <div style="font-size: 0.92rem; color: #e4e4e7; margin: 0.3rem 0; line-height: 1.5;">${probFullHtml}</div>
                  <div style="font-size: 0.72rem; color: #71717a;">復習${c.repetitions}回 / 次回間隔${c.interval}日 / lapses${c.lapses}</div>
                </div>
                <div style="display: flex; flex-direction: column; gap: 0.4rem; flex-shrink: 0;">
                  <button type="button" class="lb-btn-correct" data-key="${_escAttr(c.key)}" data-sid="${_escAttr(studentId)}" style="background: #10b981; color: white; border: none; padding: 0.4rem 0.8rem; border-radius: 6px; font-weight: 700; cursor: pointer; font-size: 0.8rem;">✓ 正解</button>
                  <button type="button" class="lb-btn-wrong" data-key="${_escAttr(c.key)}" data-sid="${_escAttr(studentId)}" style="background: #ef4444; color: white; border: none; padding: 0.4rem 0.8rem; border-radius: 6px; font-weight: 700; cursor: pointer; font-size: 0.8rem;">✗ 不正解</button>
                </div>
              </div>
              ${interactiveHtml}
              ${c.answer ? `<details style="margin-top: 0.5rem; font-size: 0.82rem;"><summary style="cursor: pointer; color: #a78bfa;">📖 解答を見る</summary><div style="padding: 0.5rem; background: rgba(0,0,0,0.3); border-radius: 6px; margin-top: 0.3rem; color: #cbd5e1;">${ansHtml}${c.explanation ? `<br><br><strong>解説:</strong> ${explHtml}` : ''}</div></details>` : ''}
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
    // 🧮 2026-06-04 文字化け横展開: 理系カード(数学/物理/化学/生物)の LaTeX \(..\)/\[..\]/$$ を KaTeX 組版。
    //   ※ 単一 $ は英語カードの通貨表記($840 等)誤組版を避けるため delimiter に入れない (理系は \( を使う)。
    _lbApplyKatex(el);
    // ✅ 2026-05-22 致命 fix: data-* + event 委任で click ハンドラを必ず attach
    // (旧 inline onclick は問題文の ' / " で JS が壊れて 79 件全カードが silent fail していた)
    if (!el.dataset.lbHandlerAttached) {
      el.addEventListener('click', (ev) => {
        // 🆕 2026-05-22 塾長指示: 選択肢ボタン (lb-choice-btn) → 自動採点 + markCard
        const choiceBtn = ev.target.closest('button.lb-choice-btn');
        if (choiceBtn) {
          ev.preventDefault();
          const details = choiceBtn.closest('details.lb-interactive');
          if (!details) return;
          const key = details.dataset.key;
          const sid = details.dataset.sid || 'guest';
          const correctLetter = details.dataset.correct || '';
          const chosen = choiceBtn.dataset.choice || '';
          if (!key) return;
          const isCorrect = correctLetter && chosen === correctLetter;
          // フィードバック表示
          const feedback = details.querySelector('.lb-feedback');
          if (feedback) {
            feedback.style.display = '';
            if (isCorrect) {
              feedback.style.background = 'rgba(16,185,129,0.20)';
              feedback.style.color = '#86efac';
              feedback.textContent = `✅ 正解! (${correctLetter}) — 1.5 秒後に SRS が更新されます`;
            } else if (correctLetter) {
              feedback.style.background = 'rgba(239,68,68,0.20)';
              feedback.style.color = '#fca5a5';
              feedback.textContent = `❌ 不正解 (あなたの選択: ${chosen} / 正解: ${correctLetter}) — 1.5 秒後に SRS が更新されます`;
            } else {
              feedback.style.background = 'rgba(251,191,36,0.20)';
              feedback.style.color = '#fde68a';
              feedback.textContent = `⚠️ 正解情報が登録されていないので採点できません。手動で「✓ 正解 / ✗ 不正解」を押してください`;
            }
          }
          // 選択肢 button を視覚化 + disable
          details.querySelectorAll('button.lb-choice-btn').forEach(b => {
            b.disabled = true;
            b.style.cursor = 'default';
            if (correctLetter && b.dataset.choice === correctLetter) {
              b.style.background = 'rgba(16,185,129,0.30)';
              b.style.borderColor = 'rgba(16,185,129,0.60)';
              b.style.color = '#fff';
            } else if (b === choiceBtn) {
              b.style.background = 'rgba(239,68,68,0.30)';
              b.style.borderColor = 'rgba(239,68,68,0.60)';
              b.style.color = '#fff';
            } else {
              b.style.opacity = '0.4';
            }
          });
          // 正解情報があれば 1.5 秒後に SRS 更新
          if (correctLetter) {
            setTimeout(() => {
              try { markCard(key, !!isCorrect, sid); } catch (e) { console.warn('LB.markCard (choice) failed:', e); }
            }, 1500);
          }
          return;
        }
        // 既存の手動「正解/不正解」ボタン (記述式 fallback)
        const btn = ev.target.closest('button.lb-btn-correct, button.lb-btn-wrong');
        if (!btn) return;
        ev.preventDefault();
        const key = btn.dataset.key;
        const sid = btn.dataset.sid || 'guest';
        const isCorrect = btn.classList.contains('lb-btn-correct');
        if (!key) return;
        try { markCard(key, isCorrect, sid); } catch (e) { console.warn('LB.markCard failed:', e); }
      });
      el.dataset.lbHandlerAttached = '1';
    }
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
    analyzeStudyTimes,
    recommendStudyTime,
    renderStudyTimeWidget,
    // テスト用
    _read, _write, _todayStr,
  };
})();
