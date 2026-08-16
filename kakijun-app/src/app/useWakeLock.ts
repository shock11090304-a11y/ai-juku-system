/**
 * 練習中のスリープ防止 (§12.7)。
 * ★iPadOS 16〜18.3 のホーム画面 Web アプリでは request が失敗するのが正常系
 * (WebKit bug 254545)。失敗しても何も起きないこと・例外で落ちないことが要件。
 * 画面遷移や visibilitychange での復帰時に再取得を試みる。
 */
import { useEffect } from 'react';

export function usePracticeWakeLock(): void {
  useEffect(() => {
    let lock: WakeLockSentinel | null = null;
    let disposed = false;

    const acquire = async () => {
      try {
        if (
          !disposed &&
          'wakeLock' in navigator &&
          document.visibilityState === 'visible'
        ) {
          lock = await navigator.wakeLock.request('screen');
        }
      } catch {
        // 効かない環境では静かに諦める (§12.7)
      }
    };

    const onVisibility = () => {
      if (document.visibilityState === 'visible') void acquire();
    };

    void acquire();
    document.addEventListener('visibilitychange', onVisibility);
    return () => {
      disposed = true;
      document.removeEventListener('visibilitychange', onVisibility);
      void lock?.release().catch(() => {});
    };
  }, []);
}
