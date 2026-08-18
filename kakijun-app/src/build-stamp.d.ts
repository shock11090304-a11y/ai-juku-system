/** vite.config.ts の define で注入されるビルド刻印 (キャッシュ切り分け用) */
declare const __BUILD_STAMP__: string;

// vite-plugin-pwa の仮想モジュール (SW 登録)
declare module 'virtual:pwa-register' {
  export function registerSW(options?: {
    immediate?: boolean;
    onRegisteredSW?: (url: string, reg: ServiceWorkerRegistration | undefined) => void;
    onNeedRefresh?: () => void;
    onOfflineReady?: () => void;
  }): (reloadPage?: boolean) => Promise<void>;
}
