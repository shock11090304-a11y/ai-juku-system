import { defineConfig } from '@playwright/test';

// 本番ビルド (vite preview) に対して E2E を回す。
// 実行前に `npm run build` が必要（webServer が preview を起動する）
export default defineConfig({
  testDir: './e2e',
  timeout: 60_000,
  retries: 1,
  use: {
    baseURL: 'http://localhost:4173',
    viewport: { width: 1180, height: 820 }, // iPad 横向き相当
  },
  webServer: {
    command: 'npx vite preview --port 4173 --strictPort',
    url: 'http://localhost:4173',
    reuseExistingServer: !process.env.CI,
  },
});
