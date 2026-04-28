/**
 * cache-purge.js — 古い Service Worker / Cache を全削除
 *
 * 背景: 過去に pwa.js が ENABLE_SW=true だった時期に、ユーザーの端末に
 * Service Worker が登録された。後で ENABLE_SW=false に変更したが、
 * pwa.js を読まないページ (mypage.html など) では unregister が動かず、
 * 古いSWが古い HTML/CSS/JS をキャッシュから返し続けていた。
 *
 * その結果「ボタンが押せない」「画面が古い」などの不具合が発生していた。
 *
 * このスクリプトは <head> の先頭で読み込み、レンダリング前に SW + Cache を
 * 完全に削除する。古いコードを表示していた疑いがある場合は、1回だけ自動リロード。
 *
 * すべてのページ (特に生徒向けページ) で読み込む想定。
 */
(function purgeStaleServiceWorker() {
  try {
    if (!('serviceWorker' in navigator)) return;
    navigator.serviceWorker.getRegistrations().then(function (regs) {
      if (regs.length > 0) {
        console.warn('[cache-purge] Unregistering', regs.length, 'stale service worker(s)');
        return Promise.all(regs.map(function (r) { return r.unregister(); }));
      }
    }).then(function () {
      if (typeof caches !== 'undefined') {
        return caches.keys().then(function (keys) {
          if (keys.length > 0) {
            console.warn('[cache-purge] Deleting', keys.length, 'stale cache(s)');
            return Promise.all(keys.map(function (k) { return caches.delete(k); }));
          }
        });
      }
    }).then(function () {
      // 🔒 リロードループ防止 (2026-04-28 強化):
      //  - sessionStorage は Safari private mode / タブ切替で消える → localStorage に変更
      //  - bfcache/prefetch でも transferSize=0 → 誤検知の主因。nav.type で除外
      //  - 一定期間 (10分) 内に 1 回までに制限
      try {
        var nav = performance.getEntriesByType('navigation')[0];
        if (!nav) return;
        // bfcache (back_forward) / prerender は transferSize=0 が正常 → スキップ
        if (nav.type === 'back_forward' || nav.type === 'prerender') return;
        if (nav.transferSize !== 0) return;
        // navigation が成功している (200 系応答) かを確認
        // duration が極端に短い (=0) の場合は計測未対応 → スキップ
        if (nav.duration === 0) return;

        var KEY = 'ai_juku_sw_purge_log_v2';
        var WINDOW_MS = 10 * 60 * 1000; // 10分
        var MAX_RELOADS = 1;
        var now = Date.now();
        var log = [];
        try { log = JSON.parse(localStorage.getItem(KEY) || '[]'); } catch (_) {}
        log = log.filter(function (t) { return (now - t) < WINDOW_MS; });
        if (log.length >= MAX_RELOADS) {
          console.warn('[cache-purge] Reload throttled (already reloaded ' + log.length + ' time(s) in last 10min)');
          return;
        }
        log.push(now);
        localStorage.setItem(KEY, JSON.stringify(log));
        console.warn('[cache-purge] Stale render suspected (transferSize=0, type=' + nav.type + ') — reloading');
        location.reload();
      } catch (e) { /* iOS 古いバージョンで fail しても無視 */ }
    }).then(function () {
      // 🆕 サーバー側 cache_version との照合 (CEO ダッシュ「全生徒キャッシュ強制パージ」と連動)
      // サーバーが新しい version を発行していたら caches 削除 + 強制リロード
      try {
        var backend = (window.location.hostname === 'localhost' && window.location.port === '8090')
          ? 'http://localhost:8000' : window.location.origin;
        fetch(backend + '/api/cache-version', { cache: 'no-store' }).then(function (res) {
          if (!res.ok) return;
          return res.json();
        }).then(function (data) {
          if (!data || !data.version) return;
          var serverVer = data.version;
          var localVer = localStorage.getItem('ai_juku_cache_version');
          if (localVer === serverVer) return; // 同一なら何もしない
          // 新しい version → caches 削除 + reload (sessionStorage の reload-once flag は別管理)
          var REL = 'ai_juku_force_reload_' + serverVer;
          if (sessionStorage.getItem(REL)) {
            // 同じ version で 2回目はスキップ (無限 reload 防止)
            localStorage.setItem('ai_juku_cache_version', serverVer);
            return;
          }
          sessionStorage.setItem(REL, '1');
          localStorage.setItem('ai_juku_cache_version', serverVer);
          console.warn('[cache-purge] New cache_version detected: ' + (localVer || 'none') + ' → ' + serverVer + ' — purging + reloading');
          if (typeof caches !== 'undefined') {
            caches.keys().then(function (keys) {
              return Promise.all(keys.map(function (k) { return caches.delete(k); }));
            }).finally(function () { location.reload(); });
          } else {
            location.reload();
          }
        }).catch(function () { /* オフライン時は何もしない */ });
      } catch (e) { /* fetch 不可なブラウザは無視 */ }
    }).catch(function (e) {
      console.warn('[cache-purge] cleanup failed:', e);
    });
  } catch (e) { /* 古いブラウザで fail しても無視 */ }
})();
