// Service Worker — AI学習コーチ塾
// 一時的なキャッシュ完全無効化版（v4 nuke）
//
// 経緯: PWA SW が古い HTML/JS を返し続け、CEO ダッシュボードに
// デモデータが表示される問題が発生。塾長が新規生徒登録機能や
// MRR内訳を見られなかった。
//
// 対処: 新 SW (v4) が install/activate 時に
//   1) 旧 cache を全削除
//   2) 自分自身を unregister
//   3) 制御下のクライアントを reload
// することでクライアント側を一発で回復させる。
// 以後、PWA キャッシュは無効（オフライン動作なし）。
const VERSION = 'v4-20260426-nuke';

self.addEventListener('install', () => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    try {
      const keys = await caches.keys();
      await Promise.all(keys.map(k => caches.delete(k)));
    } catch (e) {}
    try { await self.registration.unregister(); } catch (e) {}
    try {
      const list = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
      list.forEach(c => { try { c.navigate(c.url); } catch (e) {} });
    } catch (e) {}
  })());
});

// fetch リスナーなし → SW は HTTP リクエストに介入しない
// （activate 完了後は unregister 済みなのでこのファイルは
//  ロードされない。registration が残っている短期間のみ
//  network 直結で動作する）
