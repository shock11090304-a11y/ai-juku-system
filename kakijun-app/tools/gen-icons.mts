/**
 * PWA アイコン生成 (§12.5)。SVG を Chromium で描画して PNG 化する。
 *   npx vite-node tools/gen-icons.mts
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from '@playwright/test';

const here = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.join(here, '../public/icons');
fs.mkdirSync(outDir, { recursive: true });

/** maskable は端が切られるので余白を広く取る */
function svg(size: number, maskable: boolean): string {
  const r = maskable ? 0 : size * 0.18;
  const cx = size / 2;
  const glyphSize = maskable ? size * 0.5 : size * 0.58;
  const penW = size * 0.055;
  return `<!doctype html><meta charset="utf-8"><style>body{margin:0}</style>
<svg width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#ffcc80"/>
      <stop offset="1" stop-color="#ffb74d"/>
    </linearGradient>
  </defs>
  <rect width="${size}" height="${size}" rx="${r}" fill="url(#bg)"/>
  <circle cx="${cx}" cy="${cx}" r="${size * 0.36}" fill="#fffdf7"/>
  <text x="${cx}" y="${cx + glyphSize * 0.03}" font-family="IPAGothic, sans-serif"
        font-size="${glyphSize}" font-weight="bold" fill="#37474f"
        text-anchor="middle" dominant-baseline="central">あ</text>
  <g transform="translate(${size * 0.63}, ${size * 0.6}) rotate(40)">
    <rect x="${-penW / 2}" y="${-size * 0.16}" width="${penW}" height="${size * 0.26}"
          rx="${penW / 2}" fill="#e05d5d"/>
    <path d="M ${-penW / 2} ${size * 0.1} L 0 ${size * 0.16} L ${penW / 2} ${size * 0.1} Z"
          fill="#8d6e63"/>
  </g>
</svg>`;
}

const browser = await chromium.launch();
const page = await browser.newPage();
const targets: [string, number, boolean][] = [
  ['icon-192.png', 192, false],
  ['icon-512.png', 512, false],
  ['icon-maskable-512.png', 512, true],
  ['apple-touch-icon.png', 180, true], // iOS は自前で角丸にするので全面塗り
];
for (const [name, size, maskable] of targets) {
  await page.setViewportSize({ width: size, height: size });
  await page.setContent(svg(size, maskable));
  await page.screenshot({
    path: path.join(outDir, name),
    clip: { x: 0, y: 0, width: size, height: size },
    omitBackground: !maskable,
  });
  console.log('generated', name);
}
await browser.close();
