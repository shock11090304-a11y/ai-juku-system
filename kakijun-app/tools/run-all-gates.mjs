/**
 * ★ かきじゅんの検査を回す入口はこの1本。
 *   node tools/run-all-gates.mjs [--no-browser]
 *
 * リポジトリの決まり (CLAUDE.md「検査は run_all_gates.py に寄せる」) に合わせ、
 * 「何を回したか」を必ず印字し、1つでも落ちたら 1 で終わる。
 * ★書いたのに誰も呼んでいない検査を作らないため、新しい検査はここに足すこと。
 *
 * --no-browser: Chromium が要る検査を飛ばす (字形の検査は全部これに当たる)。
 */
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const appDir = path.join(here, '..');
const NO_BROWSER = process.argv.includes('--no-browser');

/** [表示名, コマンド, ブラウザが要るか] */
const GATES = [
  ['型検査 (tsc)', ['npx', 'tsc', '--noEmit'], false],
  ['単体テスト (vitest)', ['npx', 'vitest', 'run'], false],
  ['本番ビルド', ['npx', 'vite', 'build'], false],
  ['E2E (実ブラウザ・お手本の画素まで見る)', ['npx', 'playwright', 'test'], true],
  [
    '書き出しの点がお手本の墨に乗っているか',
    ['npx', 'vite-node', 'tools/check-start-dots.mts'],
    true,
  ],
  [
    '濁点・半濁点がお手本の記号に乗っているか',
    ['npx', 'vite-node', 'tools/check-mark-clearance.mts'],
    true,
  ],
];

console.log(`かきじゅん 検査一覧 (${GATES.length}本)${NO_BROWSER ? ' ※ブラウザ検査は飛ばす' : ''}`);
for (const [name, cmd, needsBrowser] of GATES) {
  console.log(`  ${needsBrowser && NO_BROWSER ? '-' : '・'} ${name}  [${cmd.join(' ')}]`);
}
console.log('');

const results = [];
for (const [name, cmd, needsBrowser] of GATES) {
  if (needsBrowser && NO_BROWSER) {
    results.push({ name, status: 'SKIP' });
    continue;
  }
  process.stdout.write(`── ${name} ...\n`);
  const r = spawnSync(cmd[0], cmd.slice(1), { cwd: appDir, stdio: 'inherit' });
  results.push({ name, status: r.status === 0 ? 'PASS' : 'FAIL', code: r.status });
}

console.log('\n===== まとめ =====');
for (const r of results) {
  console.log(`  ${r.status.padEnd(4)} ${r.name}${r.code ? ` (exit ${r.code})` : ''}`);
}
const failed = results.filter((r) => r.status === 'FAIL');
const skipped = results.filter((r) => r.status === 'SKIP');
if (skipped.length) {
  console.log(`\n★ ${skipped.length}本は回していない。字形の検査は手元で --no-browser 無しで回すこと。`);
}
// 目視QAは自動化できないので、やり方だけ必ず出す (HANDOFF §7-1)
console.log(
  '\n目視QA (自動検査が緑でも見た目が壊れていることがある):\n' +
    '  npx vite preview --port 4173 &\n' +
    '  node tools/qa-sheet.mjs --out /tmp/qa            # 子どもが見る画面そのもの\n' +
    '  npx vite-node tools/render/overlay-sheet.mts     # お手本と判定線の重ね合わせ',
);
if (failed.length) {
  console.log(`\n★ ${failed.length}本 落ちた`);
  process.exit(1);
}
console.log('\n全部通った');
// 検査ファイルの取りこぼし検出: tools/check* があるのに一覧に無いものを出す
const listed = new Set(GATES.flatMap(([, cmd]) => cmd).filter((a) => a.startsWith('tools/')));
const orphans = fs
  .readdirSync(path.join(appDir, 'tools'))
  .filter((f) => /^(check|verify|validate|audit)/.test(f))
  .map((f) => `tools/${f}`)
  .filter((f) => !listed.has(f));
if (orphans.length) {
  console.log(`\n★ 一覧に入っていない検査がある (誰も呼んでいない): ${orphans.join(' ')}`);
  process.exit(1);
}
