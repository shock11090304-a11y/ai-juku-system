// Service Worker — AI学習コーチ塾 PWA
const VERSION = 'v2-20260422';
const CACHE = `ai-juku-${VERSION}`;

// 初回訪問時にキャッシュする重要ファイル
const ASSETS = [
  '/',
  '/index.html',
  '/lp.html',
  '/style.css',
  '/lp.css',
  '/app.js',
  '/analytics.js',
  '/articles.js',
  '/manifest.json',
  '/icon-192.svg',
  '/icon-512.svg',
];

// Install: 即座にskipWaiting（旧SWを上書き）
self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(ASSETS)).catch(() => {}));
});

// Activate: 全てのcacheを削除し、即座にclient制御
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.map((k) => caches.delete(k)))  // 全キャッシュ削除
    ).then(() => self.clients.claim())
  );
});

// Fetch (network-first for API, cache-first for static)
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Don't cache API calls
  if (url.pathname.startsWith('/api/') || url.host !== self.location.host) {
    return;  // Use default network fetch
  }

  // For HTML: network-first (always get latest)
  if (request.mode === 'navigate' || request.headers.get('accept')?.includes('text/html')) {
    event.respondWith(
      fetch(request)
        .then((res) => {
          const copy = res.clone();
          caches.open(CACHE).then((cache) => cache.put(request, copy));
          return res;
        })
        .catch(() => caches.match(request).then((r) => r || caches.match('/index.html')))
    );
    return;
  }

  // JS/CSSは常にnetwork-firstにしてキャッシュ問題回避
  if (request.url.endsWith('.js') || request.url.endsWith('.css')) {
    event.respondWith(
      fetch(request).then((res) => {
        if (res && res.status === 200) {
          const copy = res.clone();
          caches.open(CACHE).then((cache) => cache.put(request, copy));
        }
        return res;
      }).catch(() => caches.match(request))
    );
    return;
  }

  // その他のassets: cache-first
  event.respondWith(
    caches.match(request).then((cached) => {
      return cached || fetch(request).then((res) => {
        if (res && res.status === 200) {
          const copy = res.clone();
          caches.open(CACHE).then((cache) => cache.put(request, copy));
        }
        return res;
      }).catch(() => cached);
    })
  );
});

// Push notifications (optional, future use)
self.addEventListener('push', (event) => {
  if (!event.data) return;
  const payload = event.data.json();
  event.waitUntil(
    self.registration.showNotification(payload.title || 'AI学習コーチ塾', {
      body: payload.body || '',
      icon: '/icon-192.svg',
      badge: '/icon-192.svg',
      data: payload.url || '/',
    })
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(clients.openWindow(event.notification.data || '/'));
});
