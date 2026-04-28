// ==========================================================================
// 🛡️ フロントエンド エラー実時間監視 (2026-04-27)
// ==========================================================================
// 全顧客接触ページ (lp/checkout/mypage/english-exam 等) に <head> 先頭で読込み、
// uncaught JS error / unhandled Promise rejection を /api/js-error に POST して
// 本番で「ユーザのブラウザでだけ起きている JS エラー」を即時検知する。
//
// 経緯: 2026-04-27 に checkout.js の null.checked = true で TypeError が出て
// form submit listener 全体が登録されない致命バグが、ユーザ離脱という形でしか
// 検知できず数時間放置された (PV あるのに form_submit ゼロという間接シグナルでのみ警告)。
// 直接シグナル (実際の JS エラー) を取れる仕組みが無かったのが反省点。
// ==========================================================================
(function() {
  'use strict';
  if (window.__errorMonitorInitialized) return;
  window.__errorMonitorInitialized = true;

  var BACKEND = window.location.origin.includes(':8090')
    ? 'http://localhost:8000'
    : window.location.origin;
  var sessionId = (function() {
    try {
      var s = sessionStorage.getItem('error_session_id');
      if (s) return s;
      s = 's_err_' + Math.random().toString(36).slice(2, 12);
      sessionStorage.setItem('error_session_id', s);
      return s;
    } catch (e) { return 's_err_anon'; }
  })();

  // 同一 page で同一エラーを連発させないための簡易デバウンス
  var sentSignatures = new Set();
  var sendCount = 0;
  var MAX_SEND_PER_PAGELOAD = 20;

  function reportError(payload) {
    if (sendCount >= MAX_SEND_PER_PAGELOAD) return;
    var sig = (payload.message || '') + '|' + (payload.source || '') + ':' + (payload.lineno || '');
    if (sentSignatures.has(sig)) return;
    sentSignatures.add(sig);
    sendCount++;

    try {
      // sendBeacon が使えるなら page unload 時にも漏れない
      var body = JSON.stringify(payload);
      if (navigator.sendBeacon) {
        var blob = new Blob([body], { type: 'application/json' });
        navigator.sendBeacon(BACKEND + '/api/js-error', blob);
      } else {
        fetch(BACKEND + '/api/js-error', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: body,
          keepalive: true,
        }).catch(function() {});
      }
    } catch (e) {
      // 自分が発したエラーで再帰しないよう静かに失敗
    }
  }

  // 1. uncaught JS error
  window.addEventListener('error', function(e) {
    // resource load error (img, script の 404 等) は除外
    if (e.target && e.target !== window && (e.target.tagName === 'IMG' || e.target.tagName === 'SCRIPT' || e.target.tagName === 'LINK')) {
      var url = e.target.src || e.target.href || 'unknown';
      // 空 src="" / href="" は HTML5 仕様上ブラウザが current document URL を再 fetch
      // しに行き、本物のエラーではないのに大量に「Failed to load: <自分自身>」と
      // 報告される (2026-04-28 incident)。検出して除外する。
      if (url === 'unknown' || url === '' || url === location.href) return;
      // 重要度の分類:
      //  - critical: 同一 origin の HTML/main JS/CSS が読めない (= ユーザが画面を見られない)
      //  - low:     CDN リソース (KaTeX等) や img の遅延読み込み失敗 (ユーザ影響限定的)
      var severity = 'low';
      try {
        var sameOrigin = url.indexOf(location.origin) === 0 || url.charAt(0) === '/';
        var isHtml = /\.html(\?|$)/i.test(url);
        var isMainCss = /\/(lp|app|index|mypage|english-exam)\.css(\?|$)/i.test(url);
        var isMainJs = e.target.tagName === 'SCRIPT' && sameOrigin && /\/(app|index|checkout|mypage)\.js(\?|$)/i.test(url);
        if (sameOrigin && (isHtml || isMainCss || isMainJs)) severity = 'critical';
      } catch (_) {}
      reportError({
        kind: 'resource_error',
        severity: severity,
        message: 'Failed to load: ' + url,
        tag: e.target.tagName,
        page: location.pathname + location.search,
        user_agent: (navigator.userAgent || '').slice(0, 200),
        session_id: sessionId,
        ts: new Date().toISOString(),
      });
      return;
    }
    reportError({
      kind: 'js_error',
      message: (e.message || '') + '',
      source: (e.filename || '') + '',
      lineno: e.lineno || 0,
      colno: e.colno || 0,
      stack: e.error && e.error.stack ? (e.error.stack + '').slice(0, 2000) : '',
      page: location.pathname + location.search,
      user_agent: (navigator.userAgent || '').slice(0, 200),
      session_id: sessionId,
      ts: new Date().toISOString(),
    });
  }, true);

  // 2. unhandled Promise rejection (fetch().catch() 漏れなど)
  window.addEventListener('unhandledrejection', function(e) {
    var reason = e.reason;
    var msg = '';
    var stack = '';
    if (reason instanceof Error) {
      msg = reason.message || (reason + '');
      stack = (reason.stack || '').slice(0, 2000);
    } else {
      try { msg = JSON.stringify(reason).slice(0, 500); } catch (_) { msg = (reason + '').slice(0, 500); }
    }
    reportError({
      kind: 'promise_rejection',
      message: msg,
      stack: stack,
      page: location.pathname + location.search,
      user_agent: (navigator.userAgent || '').slice(0, 200),
      session_id: sessionId,
      ts: new Date().toISOString(),
    });
  });

  // 3. ヘルスチェック: ページロード時に 'page_loaded_ok' イベントを送って
  //    生存確認 (これが来てない page_view は JS が早期 fail している可能性)
  window.addEventListener('load', function() {
    try {
      fetch(BACKEND + '/api/track', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: 'page_loaded_ok',
          props: { page: location.pathname, ts: Date.now() },
          session_id: sessionId,
        }),
      }).catch(function() {});
    } catch (e) {}
  });
})();
