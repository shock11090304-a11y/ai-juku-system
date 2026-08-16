import React from 'react';
import ReactDOM from 'react-dom/client';
import { App } from './app/App';
import './styles/global.css';

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
