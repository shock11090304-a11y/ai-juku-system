/// <reference types="vitest/config" />
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';

// base './' なので、どのパス（サブディレクトリ配信・file 配布・別ドメイン）でも動く
export default defineConfig({
  base: './',
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['icons/apple-touch-icon.png'],
      manifest: {
        name: 'かきじゅん れんしゅう',
        short_name: 'かきじゅん',
        display: 'standalone',
        orientation: 'landscape',
        background_color: '#FFFDF7',
        theme_color: '#FFB74D',
        start_url: './',
        icons: [
          { src: './icons/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: './icons/icon-512.png', sizes: '512x512', type: 'image/png' },
          {
            src: './icons/icon-maskable-512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'maskable',
          },
        ],
      },
      workbox: {
        // 音声・画像・JSON まで全アセットを事前キャッシュして完全オフラインで動かす (§12.5)
        globPatterns: ['**/*.{js,css,html,png,svg,webp,mp3,json,webmanifest,woff2}'],
        maximumFileSizeToCacheInBytes: 5 * 1024 * 1024,
      },
    }),
  ],
  test: {
    environment: 'node',
    include: ['src/**/__tests__/**/*.test.ts'],
  },
});
