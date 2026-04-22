// ==========================================================================
// Analytics — GA4 + カスタムイベントトラッキング
// ==========================================================================
// 使い方:
// 1. Google Analytics 4 のプロパティを作成し、測定IDを取得 (G-XXXXXXXX)
// 2. `window.GA4_ID` をHTML内で設定するか、ここに直接書く
// 3. このファイルを全ページの <head> で読み込む: <script src="analytics.js"></script>

(function() {
  const GA4_ID = window.GA4_ID || 'G-XXXXXXXX';  // 本番デプロイ時に正しいIDに置き換え
  const BACKEND_URL = window.location.hostname === 'localhost' && window.location.port === '8090'
    ? 'http://localhost:8000'
    : window.location.origin;

  // --- Google Analytics 4 loader ---
  if (GA4_ID !== 'G-XXXXXXXX') {
    const script = document.createElement('script');
    script.async = true;
    script.src = `https://www.googletagmanager.com/gtag/js?id=${GA4_ID}`;
    document.head.appendChild(script);

    window.dataLayer = window.dataLayer || [];
    window.gtag = function() { dataLayer.push(arguments); };
    gtag('js', new Date());
    gtag('config', GA4_ID, {
      anonymize_ip: true,
      cookie_flags: 'SameSite=None;Secure'
    });
  }

  // --- Custom event tracker (also posts to backend) ---
  const sessionId = sessionStorage.getItem('aj_session_id') ||
    (() => { const s = 's_' + Math.random().toString(36).slice(2, 10); sessionStorage.setItem('aj_session_id', s); return s; })();

  window.track = function(eventName, props = {}) {
    // GA4
    if (typeof gtag === 'function') {
      gtag('event', eventName, props);
    }
    // Backend
    fetch(`${BACKEND_URL}/api/track`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: eventName, props, session_id: sessionId }),
    }).catch(() => {});
  };

  // --- Auto-track page view ---
  window.track('page_view', {
    page_path: window.location.pathname,
    page_title: document.title,
    referrer: document.referrer,
  });

  // --- Auto-track outbound link clicks ---
  document.addEventListener('click', (e) => {
    const link = e.target.closest('a');
    if (!link) return;
    const href = link.getAttribute('href') || '';
    if (href.startsWith('http') && !href.includes(window.location.hostname)) {
      window.track('outbound_click', { url: href, text: link.textContent.trim().slice(0, 50) });
    }
    if (link.classList.contains('btn-primary')) {
      window.track('cta_click', {
        text: link.textContent.trim().slice(0, 50),
        href,
        page: window.location.pathname,
      });
    }
  });

  // --- Track form submissions ---
  document.addEventListener('submit', (e) => {
    const form = e.target;
    window.track('form_submit', { form_id: form.id || 'unknown', page: window.location.pathname });
  });

  // --- Track scroll depth (25/50/75/100) ---
  const depths = { 25: false, 50: false, 75: false, 100: false };
  window.addEventListener('scroll', () => {
    const pct = (window.scrollY + window.innerHeight) / document.body.scrollHeight * 100;
    [25, 50, 75, 100].forEach(t => {
      if (!depths[t] && pct >= t) {
        depths[t] = true;
        window.track('scroll_depth', { percent: t });
      }
    });
  }, { passive: true });
})();
