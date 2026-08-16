import React from 'react';
import ReactDOM from 'react-dom/client';
import { App } from './app/App';
import './styles/global.css';

// iOS Safari の ITP によるストレージ削除に備えて永続化を要求する (§12.6)
if (navigator.storage?.persist) {
  navigator.storage.persist().catch(() => {});
}

// ダブルタップズームの抑制 (§12.1)。touch-action だけでは iOS Safari で防げないことがある
let lastTouchEnd = 0;
document.addEventListener(
  'touchend',
  (e) => {
    const now = Date.now();
    if (now - lastTouchEnd <= 300) e.preventDefault();
    lastTouchEnd = now;
  },
  { passive: false },
);

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
