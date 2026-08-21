/* ==========================================================================
 * 🔥 Social Proof Banner — 社会的証明モニター
 *
 * lp.html / checkout.html / course-kokuritsu-nankan.html / pricing-compare.html
 * 等で「累計 X 人突破」等の社会的証明モニターを表示。
 * ★2026-07-02 塾長方針: 偽装の「残り枠 N 名」表示は撤去(残席は lp の実数連動カウンター /api/founders/count に一本化)。
 *
 * 数値は plans.js の PLAN_CONFIG.socialProof で集中管理 (塾長が直接編集可)。
 *
 * 使い方: HTML に <div data-social-proof></div> を置けば自動描画。
 * オプション: data-social-proof="compact" で短縮表示。
 * ========================================================================== */
(function () {
  function _animateCount(el, target, duration) {
    if (!el || target === 0) return;
    const start = Math.max(0, target - Math.min(20, target));  // 直近 20 名分カウントアップ
    const diff = target - start;
    if (diff <= 0) { el.textContent = target.toLocaleString('ja-JP'); return; }
    const stepMs = 40;
    const steps = Math.max(1, Math.floor(duration / stepMs));
    let current = start;
    el.textContent = current.toLocaleString('ja-JP');
    const inc = diff / steps;
    let i = 0;
    const timer = setInterval(() => {
      i++;
      current = Math.min(target, Math.round(start + inc * i));
      el.textContent = current.toLocaleString('ja-JP');
      if (i >= steps) clearInterval(timer);
    }, stepMs);
  }

  function _renderBanner(el, mode) {
    if (!window.PLAN_CONFIG || !window.PLAN_CONFIG.socialProof) return;
    const sp = window.PLAN_CONFIG.socialProof;
    if (sp.showBanner === false) { el.style.display = 'none'; return; }

    const isCompact = mode === 'compact';
    if (isCompact) {
      el.innerHTML = `
        <div style="display:inline-flex; align-items:center; gap:0.5rem; padding:0.4rem 0.9rem; background:linear-gradient(135deg, rgba(34,197,94,0.15), rgba(59,130,246,0.1)); border:1px solid rgba(34,197,94,0.4); border-radius:999px; font-size:0.78rem; color:#86efac; font-weight:700;">
          <span style="width:8px; height:8px; background:#34d399; border-radius:50%; animation:sp-pulse 2s infinite;"></span>
          <span>🔥 累計 <strong data-sp-total style="color:#fbbf24; font-size:1rem;">${sp.totalUsers}</strong> 人突破</span>
        </div>`;
    } else {
      // 🚨 2026-08-21 撤去: 「現在閲覧中 N 人」は plans.js の onlineNow
      //   (自ら「擬似値」と注記された固定値 12) を、脈打つ緑ドット付きでライブ表示していた。
      //   2026-07-02 の「偽装の残り枠表示は撤去」方針と正面から矛盾する。実数が取れるまで出さない。
      //   ★説明は **JS コメント**に置くこと。テンプレートリテラルの中に HTML コメントで書くと、
      //     内部の言葉がそのまま訪問者のページソースに出る (一度やりかけた)。
      el.innerHTML = `
        <div style="background:linear-gradient(135deg, rgba(34,197,94,0.08) 0%, rgba(59,130,246,0.06) 100%); border:1px solid rgba(34,197,94,0.3); border-radius:14px; padding:0.9rem 1.2rem; margin: 0.8rem 0;">
          <div style="display:flex; flex-wrap:wrap; gap:0.5rem 1.4rem; align-items:center; justify-content:center;">
            <div style="display:flex; align-items:center; gap:0.4rem;">
              <span style="font-size:1.1rem;">🎉</span>
              <span style="color:#94a3b8; font-size:0.82rem;">累計利用者</span>
              <strong data-sp-total style="color:#fbbf24; font-size:1.15rem;">${sp.totalUsers}</strong>
              <span style="color:#fbbf24; font-size:0.82rem;">人 突破</span>
            </div>
            <div style="display:flex; align-items:center; gap:0.4rem;">
              <span style="font-size:1.1rem;">📈</span>
              <span style="color:#94a3b8; font-size:0.82rem;">今週</span>
              <strong style="color:#a78bfa; font-size:1.05rem;">${sp.thisWeekSignups}</strong>
              <span style="color:#a78bfa; font-size:0.82rem;">名 申込</span>
            </div>
          </div>
        </div>
        <style>@keyframes sp-pulse { 0%,100% { opacity:1; } 50% { opacity:0.4; } }</style>`;
    }

    // 累計人数だけアニメーション (視覚効果・最初の 1 度のみ)
    const totalEl = el.querySelector('[data-sp-total]');
    if (totalEl && !el._spAnimated) {
      el._spAnimated = true;
      _animateCount(totalEl, sp.totalUsers, 1200);
    }
  }

  function _renderAll() {
    document.querySelectorAll('[data-social-proof]').forEach((el) => {
      const mode = el.getAttribute('data-social-proof') || 'full';
      _renderBanner(el, mode);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', _renderAll);
  } else {
    _renderAll();
  }
})();
