/**
 * E2E (§13 Phase 8)。本番ビルドに対して:
 * ホーム → 文字えらび → 練習（実データをなぞって完走）→ 花丸、
 * 保護者ゲート、やり直し、戻る動線 (§14.3 どの画面からも2タップ以内でホーム)。
 */
import fs from 'node:fs';
import path from 'node:path';
import { expect, test, type Page } from '@playwright/test';
import { prepareStrokes, toCharacterDef } from '../src/engine/loader';
import type { RawCharacterDef } from '../src/engine/types';

// Playwright のトランスパイラは JSON import を解決できないので fs で読む
function loadChar(charId: string): RawCharacterDef {
  const here = path.dirname(new URL(import.meta.url).pathname);
  const file = path.join(here, '../src/data/characters/hiragana.json');
  const defs = JSON.parse(fs.readFileSync(file, 'utf8')) as RawCharacterDef[];
  const def = defs.find((d) => d.id === charId);
  if (!def) throw new Error(`not found: ${charId}`);
  return def;
}

async function traceChar(page: Page, charId: string): Promise<void> {
  const strokes = prepareStrokes(toCharacterDef(loadChar(charId)));
  const box = (await page
    .locator('[data-testid=practice-canvas]')
    .boundingBox())!;
  const toScreen = (p: { x: number; y: number }) => ({
    x: box.x + p.x * box.width,
    y: box.y + p.y * box.height,
  });
  for (const s of strokes) {
    const start = toScreen(s.pts[0]);
    await page.mouse.move(start.x, start.y);
    await page.mouse.down();
    for (let i = 1; i < 64; i += 2) {
      const p = toScreen(s.pts[i]);
      await page.mouse.move(p.x, p.y);
    }
    await page.mouse.up();
    await page.waitForTimeout(200);
  }
}

test('ホーム → ひらがな → し を完走 → 花丸 → つぎのじ', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByTestId('tile-hiragana')).toBeVisible();
  await page.click('[data-testid=tile-hiragana]');
  await page.click('[data-testid=char-hira_shi]');
  await page.waitForSelector('[data-testid=practice-canvas] canvas');
  await page.waitForTimeout(1600); // お手本アニメ

  await traceChar(page, 'hira_shi');
  await expect(page.getByTestId('celebration')).toBeVisible();
  await page.click('[data-testid=btn-next]');
  // 次の文字（す）の練習画面に進む
  await expect(page.getByTestId('celebration')).toHaveCount(0);
  await expect(page.getByTestId('practice-canvas')).toBeVisible();
});

test('カタカナ・すうじ・せんのれんしゅう のタイルが有効', async ({ page }) => {
  await page.goto('/');
  for (const t of ['katakana', 'number', 'unpitsu']) {
    await expect(page.getByTestId(`tile-${t}`)).toBeEnabled();
  }
});

test('どの画面からも2タップ以内でホームに戻れる (§14.3)', async ({ page }) => {
  await page.goto('/');
  await page.click('[data-testid=tile-number]');
  await page.click('[data-testid=char-num_3]');
  await page.waitForSelector('[data-testid=practice-canvas] canvas');
  await page.click('[data-testid=btn-back]'); // → 文字えらび
  await page.click('[data-testid=btn-back]'); // → ホーム
  await expect(page.getByTestId('tile-hiragana')).toBeVisible();
});

test('まちがった始点では画が進まない', async ({ page }) => {
  await page.goto('/');
  await page.click('[data-testid=tile-hiragana]');
  await page.click('[data-testid=char-hira_a]');
  await page.waitForSelector('[data-testid=practice-canvas] canvas');
  await page.waitForTimeout(1600);
  const box = (await page
    .locator('[data-testid=practice-canvas]')
    .boundingBox())!;
  // 中央あたり（1画目の始点から遠い場所）をタップして描こうとする
  await page.mouse.move(box.x + box.width * 0.5, box.y + box.height * 0.6);
  await page.mouse.down();
  await page.mouse.move(box.x + box.width * 0.7, box.y + box.height * 0.6);
  await page.mouse.up();
  await expect(page.getByTestId('celebration')).toHaveCount(0);
});

test('保護者ゲート: 3回誤答でホームへ / 正解でダッシュボード (§14.3)', async ({
  page,
}) => {
  await page.goto('/');
  await page.click('[data-testid=btn-gear]');
  for (let i = 0; i < 3; i++) {
    await page.click('[data-testid=key-1]'); // 積は必ず二桁なので 1 は誤答
    await page.click('[data-testid=key-OK]');
  }
  await expect(page.getByTestId('tile-hiragana')).toBeVisible();

  await page.click('[data-testid=btn-gear]');
  const q = await page.locator('text=/\\d+ × \\d+/').textContent();
  const m = q!.match(/(\d+) × (\d+)/)!;
  for (const d of String(Number(m[1]) * Number(m[2]))) {
    await page.click(`[data-testid=key-${d}]`);
  }
  await page.click('[data-testid=key-OK]');
  await expect(page.getByText('保護者メニュー')).toBeVisible();
});

test('完走の記録がリロード後も残る (§14.5)', async ({ page }) => {
  await page.goto('/');
  await page.click('[data-testid=tile-hiragana]');
  await page.click('[data-testid=char-hira_ku]');
  await page.waitForSelector('[data-testid=practice-canvas] canvas');
  await page.waitForTimeout(1600);
  await traceChar(page, 'hira_ku');
  await expect(page.getByTestId('celebration')).toBeVisible();
  // 記録は完走時に保存済み。そのままリロードして残っているかを見る
  await page.reload();
  await page.click('[data-testid=tile-hiragana]');
  // く のマスに星が1つ以上ついている（opacity 1 の ⭐ が存在する）
  const cell = page.getByTestId('char-hira_ku');
  await expect(cell).toBeVisible();
  const stars = await cell
    .locator('span span')
    .evaluateAll((els) =>
      els.filter((el) => getComputedStyle(el).opacity === '1').length,
    );
  expect(stars).toBeGreaterThanOrEqual(1);
});
