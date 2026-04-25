/**
 * 定期テスト連携 (Exam Prep) — 学校の定期テスト/中間/期末/模試の対策
 *
 * 機能:
 *  - 定期テスト登録 (学校名・科目・日付・出題範囲)
 *  - カウントダウン表示
 *  - 範囲から AI で問題自動生成 (問題ジェネレーター連携)
 *  - 進捗トラッキング (LB と連携)
 *
 * すべて localStorage ベース
 */
(function () {
  'use strict';
  const STORAGE_KEY = 'ai_juku_exam_prep__exams';

  function _read() {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]'); }
    catch { return []; }
  }
  function _write(exams) {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(exams)); }
    catch (e) { console.warn('ExamPrep storage write failed:', e); }
  }
  function _uid() {
    return 'exam_' + Date.now() + '_' + Math.floor(Math.random() * 9999);
  }
  function _daysUntil(dateStr) {
    const t = new Date(dateStr); t.setHours(0,0,0,0);
    const n = new Date(); n.setHours(0,0,0,0);
    return Math.round((t - n) / (1000*60*60*24));
  }

  function addExam(opts) {
    const exams = _read();
    const exam = {
      id: _uid(),
      schoolName: opts.schoolName || '',
      examName: opts.examName || '定期テスト',
      examDate: opts.examDate,  // YYYY-MM-DD
      subject: opts.subject || '',
      scope: opts.scope || '',  // 出題範囲のテキスト
      goalScore: opts.goalScore || null,
      createdAt: new Date().toISOString(),
      problems: [],  // 生成済み問題 (LB key の配列)
      status: 'preparing',
    };
    exams.push(exam);
    _write(exams);
    return exam;
  }

  function listExams() {
    return _read().sort((a, b) => a.examDate.localeCompare(b.examDate));
  }
  function getExam(id) {
    return _read().find(e => e.id === id);
  }
  function deleteExam(id) {
    const exams = _read().filter(e => e.id !== id);
    _write(exams);
  }
  function updateExam(id, patch) {
    const exams = _read();
    const idx = exams.findIndex(e => e.id === id);
    if (idx < 0) return null;
    exams[idx] = { ...exams[idx], ...patch };
    _write(exams);
    return exams[idx];
  }

  function getUpcoming(maxDays = 30) {
    const today = new Date().toISOString().slice(0,10);
    return _read()
      .filter(e => e.examDate >= today && _daysUntil(e.examDate) <= maxDays)
      .sort((a, b) => a.examDate.localeCompare(b.examDate));
  }

  function renderUpcomingWidget(containerId) {
    const el = document.getElementById(containerId);
    if (!el) return;
    const upcoming = getUpcoming(60);
    if (upcoming.length === 0) {
      el.innerHTML = `
        <div style="background:rgba(255,255,255,0.03);border:1px dashed rgba(255,255,255,0.15);border-radius:10px;padding:1rem;text-align:center;">
          <p style="color:#94a3b8;margin:0 0 0.5rem 0;font-size:0.9rem;">📅 次の定期テスト/模試は未登録です</p>
          <a href="exam-prep.html" style="display:inline-block;background:#6366f1;color:white;padding:0.5rem 1rem;border-radius:6px;text-decoration:none;font-size:0.85rem;font-weight:700;">テスト日程を登録</a>
        </div>`;
      return;
    }
    el.innerHTML = `
      <div style="margin-bottom:0.5rem;font-weight:800;color:#fbbf24;">📅 直近のテスト</div>
      ${upcoming.slice(0, 3).map(e => {
        const days = _daysUntil(e.examDate);
        const urgency = days <= 3 ? '#ef4444' : (days <= 7 ? '#f59e0b' : '#6366f1');
        return `
        <div style="background:rgba(255,255,255,0.04);border-left:4px solid ${urgency};border-radius:8px;padding:0.7rem 0.9rem;margin:0.4rem 0;">
          <div style="display:flex;justify-content:space-between;align-items:center;gap:0.5rem;">
            <div style="flex:1;min-width:0;">
              <div style="font-weight:700;color:#e4e4e7;font-size:0.9rem;">${e.examName}${e.subject ? ' / ' + e.subject : ''}</div>
              <div style="font-size:0.78rem;color:#a1a1aa;">${e.schoolName} · ${e.examDate}</div>
            </div>
            <div style="text-align:right;flex-shrink:0;">
              <div style="font-size:1.4rem;font-weight:900;color:${urgency};line-height:1;">あと${days}日</div>
              ${e.problems.length > 0 ? `<div style="font-size:0.72rem;color:#71717a;">対策${e.problems.length}問</div>` : ''}
            </div>
          </div>
        </div>`;
      }).join('')}
      <div style="text-align:right;margin-top:0.4rem;"><a href="exam-prep.html" style="color:#a78bfa;font-size:0.82rem;text-decoration:none;">→ すべて見る</a></div>
    `;
  }

  window.ExamPrep = {
    addExam, listExams, getExam, deleteExam, updateExam,
    getUpcoming, renderUpcomingWidget,
    _daysUntil,
  };
})();
