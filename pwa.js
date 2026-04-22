// PWA installation helper — all pages include this
(function() {
  // iframe内ではSW登録をスキップ
  if (window.top !== window.self) return;

  // 開発中はSW無効化（キャッシュ問題と反応遅延を回避）
  // 本番デプロイ時に以下のブロック全体を有効化
  const ENABLE_SW = false;
  if (!ENABLE_SW) {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.getRegistrations().then(regs => {
        regs.forEach(r => r.unregister());
      }).catch(() => {});
    }
    return;
  }

  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js').catch(() => {});
    });
  }

  // Install prompt handling
  let deferredPrompt;
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    showInstallButton();
  });

  function showInstallButton() {
    if (sessionStorage.getItem('pwa_install_dismissed')) return;

    const banner = document.createElement('div');
    banner.id = 'pwa-install-banner';
    banner.innerHTML = `
      <div class="pwa-banner-content">
        <div class="pwa-banner-icon">📱</div>
        <div class="pwa-banner-text">
          <div class="pwa-banner-title">アプリとしてインストール</div>
          <div class="pwa-banner-desc">ホーム画面に追加して、オフラインでも使えます</div>
        </div>
        <div class="pwa-banner-actions">
          <button id="pwaInstallBtn" class="pwa-btn-primary">インストール</button>
          <button id="pwaDismissBtn" class="pwa-btn-ghost">×</button>
        </div>
      </div>
    `;
    document.body.appendChild(banner);

    if (!document.getElementById('pwa-install-style')) {
      const style = document.createElement('style');
      style.id = 'pwa-install-style';
      style.textContent = `
        #pwa-install-banner {
          position: fixed;
          bottom: 1rem;
          left: 50%;
          transform: translateX(-50%);
          z-index: 1000;
          background: linear-gradient(135deg, rgba(20, 20, 40, 0.95), rgba(30, 30, 60, 0.95));
          border: 1px solid rgba(99, 102, 241, 0.4);
          border-radius: 14px;
          padding: 1rem 1.5rem;
          box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
          backdrop-filter: blur(20px);
          max-width: 500px;
          animation: slideUp 0.4s ease-out;
        }
        @keyframes slideUp {
          from { transform: translate(-50%, 100px); opacity: 0; }
          to { transform: translate(-50%, 0); opacity: 1; }
        }
        .pwa-banner-content {
          display: flex;
          align-items: center;
          gap: 1rem;
        }
        .pwa-banner-icon { font-size: 2rem; }
        .pwa-banner-text { flex: 1; }
        .pwa-banner-title {
          font-weight: 700;
          font-size: 0.95rem;
          color: #e5e7eb;
          margin-bottom: 0.2rem;
        }
        .pwa-banner-desc {
          font-size: 0.8rem;
          color: #9ca3af;
        }
        .pwa-banner-actions { display: flex; gap: 0.5rem; }
        .pwa-btn-primary {
          background: linear-gradient(135deg, #6366f1, #ec4899);
          color: white;
          border: none;
          padding: 0.6rem 1.2rem;
          border-radius: 8px;
          font-family: inherit;
          font-weight: 700;
          font-size: 0.85rem;
          cursor: pointer;
        }
        .pwa-btn-ghost {
          background: rgba(255, 255, 255, 0.05);
          color: #9ca3af;
          border: none;
          width: 32px;
          height: 32px;
          border-radius: 8px;
          cursor: pointer;
          font-size: 1.2rem;
        }
        .pwa-btn-ghost:hover { background: rgba(255, 255, 255, 0.1); color: #fff; }
        @media (max-width: 500px) {
          #pwa-install-banner { left: 1rem; right: 1rem; transform: none; max-width: none; }
          @keyframes slideUp {
            from { transform: translateY(100px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
          }
        }
      `;
      document.head.appendChild(style);
    }

    document.getElementById('pwaInstallBtn').addEventListener('click', async () => {
      if (deferredPrompt) {
        deferredPrompt.prompt();
        const { outcome } = await deferredPrompt.userChoice;
        if (window.track) window.track('pwa_install_prompt', { outcome });
        deferredPrompt = null;
      }
      banner.remove();
    });

    document.getElementById('pwaDismissBtn').addEventListener('click', () => {
      sessionStorage.setItem('pwa_install_dismissed', '1');
      banner.remove();
    });
  }

  window.addEventListener('appinstalled', () => {
    if (window.track) window.track('pwa_installed');
  });
})();
