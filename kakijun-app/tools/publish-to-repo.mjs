/**
 * 公開用: 本番ビルドをリポジトリ直下 /kakijun/ にコピーする。
 * main にマージされると Vercel が静的配信し、
 * https://trillion-ai-juku.com/kakijun/ で開けるようになる。
 *   node tools/publish-to-repo.mjs   (kakijun-app/ で実行。ビルドも行う)
 */
import { execSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const appDir = path.join(here, '..');
const dist = path.join(appDir, 'dist');
const target = path.join(appDir, '..', 'kakijun');

execSync('npx vite build', { cwd: appDir, stdio: 'inherit' });
fs.rmSync(target, { recursive: true, force: true });
fs.cpSync(dist, target, { recursive: true });
console.log(`published: ${dist} -> ${target}`);
