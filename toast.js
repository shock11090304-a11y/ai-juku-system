// 🎯 2026-05-26 audit Phase 3: 統一 toast UI helper (alert 置換)
// memory 「alert UX 冷たさ」を改善: モーダル blocking から非 blocking notification に切替。
// 使い方: showToast('保存しました', 'success') / showToast('採点エラー', 'error', 5000)
//
// 段階的置換戦略: mock-exam.js / app.js の生徒主機能を優先置換、
// 他 file の alert は次 batch で漸進的。fallback で alert も維持される。
(function () {
  'use strict';

  function ensureContainer() {
    let container = document.getElementById('ajToastContainer');
    if (container) return container;
    container = document.createElement('div');
    container.id = 'ajToastContainer';
    container.setAttribute('role', 'status');
    container.setAttribute('aria-live', 'polite');
    container.style.cssText = [
      'position:fixed',
      // 🎯 2026-05-26 audit fix: iPhone notch / Dynamic Island 衝突回避
      'top:max(1rem, env(safe-area-inset-top, 1rem))',
      'left:50%',
      'transform:translateX(-50%)',
      'z-index:99999',
      'display:flex',
      'flex-direction:column',
      'gap:0.5rem',
      'pointer-events:none',
      'max-width:90vw',
    ].join(';');
    document.body.appendChild(container);
    return container;
  }

  // 🎯 2026-05-26 audit fix (致命 J): warn の text color を dark に変更で WCAG AA contrast 4.5:1 達成。
  // warn 黄背景 + white text は 1.9:1 で読みにくい (iPhone 実機検証)。dark text に統一。
  const COLORS = {
    info:    { bg: 'linear-gradient(135deg, rgba(99,102,241,0.97), rgba(79,70,229,0.97))', text: '#ffffff' },
    success: { bg: 'linear-gradient(135deg, rgba(34,197,94,0.97), rgba(22,163,74,0.97))',  text: '#ffffff' },
    warn:    { bg: 'linear-gradient(135deg, rgba(251,191,36,0.97), rgba(245,158,11,0.97))', text: '#1f2937' },
    error:   { bg: 'linear-gradient(135deg, rgba(239,68,68,0.97), rgba(220,38,38,0.97))',  text: '#ffffff' },
  };

  const ICONS = { info: 'ℹ️', success: '✅', warn: '⚠️', error: '❌' };

  // 🎯 2026-05-26 audit fix (重大): error は技術的 message 読了時間確保で default 6s に延長
  const DEFAULT_DURATIONS = { info: 3500, success: 3500, warn: 4000, error: 6000 };

  /**
   * 統一 toast 表示。
   * @param {string} message - 表示文字列 (innerHTML ではなく textContent 経由で XSS safe)
   * @param {'info'|'success'|'warn'|'error'} type
   * @param {number} duration - ms (default 3500)
   */
  function showToast(message, type, duration) {
    if (message == null) return;
    const t = COLORS[type] ? type : 'info';
    // 🎯 type 別 default duration (error 6s で技術的 message 読了時間確保)
    const ms = (typeof duration === 'number' && duration > 0) ? duration : (DEFAULT_DURATIONS[t] || 3500);
    const container = ensureContainer();
    const toast = document.createElement('div');
    toast.style.cssText = [
      'background:' + COLORS[t].bg,
      'color:' + COLORS[t].text,
      'padding:0.85rem 1.25rem',
      'border-radius:10px',
      'font-size:0.95rem',
      'font-weight:600',
      'box-shadow:0 6px 16px rgba(0,0,0,0.35)',
      'text-align:center',
      'pointer-events:auto',
      'opacity:0',
      'transform:translateY(-0.75rem)',
      'transition:opacity 0.2s ease, transform 0.2s ease',
      'cursor:pointer',
      'display:flex',
      'align-items:center',
      'gap:0.5rem',
      'justify-content:center',
    ].join(';');
    // 🛡️ XSS safe: textContent で挿入 (HTML 解釈なし)
    const iconSpan = document.createElement('span');
    iconSpan.style.cssText = 'font-size:1.1rem; line-height:1;';
    iconSpan.textContent = ICONS[t] || ICONS.info;
    const msgSpan = document.createElement('span');
    msgSpan.textContent = String(message);
    toast.appendChild(iconSpan);
    toast.appendChild(msgSpan);
    // click で即消去
    toast.addEventListener('click', () => removeToast(toast));
    container.appendChild(toast);
    // 表示 animation
    requestAnimationFrame(() => {
      toast.style.opacity = '1';
      toast.style.transform = 'translateY(0)';
    });
    // 自動消去
    setTimeout(() => removeToast(toast), ms);
  }

  function removeToast(toast) {
    if (!toast || !toast.parentNode) return;
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(-0.75rem)';
    setTimeout(() => {
      if (toast.parentNode) toast.remove();
    }, 220);
  }

  window.showToast = showToast;
})();
