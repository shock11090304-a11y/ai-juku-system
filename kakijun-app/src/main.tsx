import React from 'react';
import ReactDOM from 'react-dom/client';
import { registerSW } from 'virtual:pwa-register';
import { App } from './app/App';
import './styles/global.css';

// ── 新しいビルドへの自動切り替え (§12.5) ─────────────────────────
// PWA は Service Worker が全アセットを事前キャッシュするので、開きっぱなしの
// タブは新しいビルドが出ても古いまま動き続ける (更新チェックはページ読み込み時
// だけ)。塾長が「直っていない」を見る原因の大半がこれだった。
//   - 1分ごと + タブが前面に戻ったときに更新を確認する
//   - 新しい SW に切り替わったら一度だけ再読み込みして新ビルドで動く
//     (練習中でも切り替える。進捗は文字の完走ごとに保存済みなので失うのは
//      書きかけの1字だけ。古いお手本で練習を続けるほうが害が大きい)
{
  let hadController = !!navigator.serviceWorker?.controller;
  navigator.serviceWorker?.addEventListener('controllerchange', () => {
    // 初回インストール時にも発火する (clientsClaim)。そこで reload すると
    // 初回訪問が二重読み込みになるので、既に SW 配下だった場合だけ reload
    if (!hadController) {
      hadController = true;
      return;
    }
    location.reload();
  });
  registerSW({
    immediate: true,
    onRegisteredSW(_url, reg) {
      const check = () => reg?.update().catch(() => {});
      setInterval(check, 60_000);
      document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible') check();
      });
    },
  });
}

// iOS Safari の ITP によるストレージ削除に備えて永続化を要求する (§12.6)
if (navigator.storage?.persist) {
  navigator.storage.persist().catch(() => {});
}

// ダブルタップズームの抑制 (§12.1)。touch-action だけでは iOS Safari で防げないことがある。
// ★ボタン等のインタラクティブ要素は preventDefault の対象外にする。
//   対象にすると 300ms 以内の連打でクリック合成が消え、保護者ゲートの
//   キーパッドや「もういっかい」連打が「押しても効かない」状態になる
let lastTouchEnd = 0;
document.addEventListener(
  'touchend',
  (e) => {
    const now = Date.now();
    const interactive = (e.target as Element | null)?.closest?.(
      'button, a, input, select, textarea',
    );
    if (now - lastTouchEnd <= 300 && !interactive) e.preventDefault();
    lastTouchEnd = now;
  },
  { passive: false },
);

/** 予期しない例外で白画面のまま固まるのを防ぐ (幼児は復帰操作ができない) */
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { failed: boolean }
> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    if (!this.state.failed) return this.props.children;
    return (
      <div
        style={{
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 24,
        }}
      >
        <div style={{ fontSize: 90 }}>🐣</div>
        <button
          onClick={() => location.reload()}
          aria-label="もういちど ひらく"
          style={{
            fontSize: 40,
            padding: '20px 44px',
            borderRadius: 24,
            background: '#ffb74d',
            boxShadow: '0 4px 12px rgba(55,71,79,0.2)',
          }}
        >
          🔄 もういちど
        </button>
      </div>
    );
  }
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>,
);
