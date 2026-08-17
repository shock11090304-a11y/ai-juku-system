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

/**
 * ★ 回帰テスト: お手本が消える事故 (2026-08-17)。
 * ResizeObserver が「寸法が変わっていないのに」発火すると canvas.width への
 * 再代入で背景層 (マス目 + お手本) が消え、誰も描き直さないまま真っ白になっていた。
 * 1字目は正常で 2字目以降が真っ白になるので、必ず「戻って別の字」まで見ること。
 * 見た目の事故なので、DOM ではなく実際の画素を数える。
 */
async function bgInk(page: Page): Promise<number> {
  return page.evaluate(() => {
    const c = document.querySelector(
      '[data-testid=practice-canvas] canvas',
    ) as HTMLCanvasElement; // 1枚目 = 背景層
    const d = c.getContext('2d')!.getImageData(0, 0, c.width, c.height).data;
    let n = 0;
    for (let i = 3; i < d.length; i += 4) if (d[i] > 0) n++;
    return n;
  });
}

test('2字目以降もお手本とマス目が消えない (背景層の画素を数える)', async ({ page }) => {
  await page.goto('/');
  await page.click('[data-testid=tile-hiragana]');
  await page.click('[data-testid=char-hira_a]');
  await page.waitForSelector('[data-testid=practice-canvas] canvas');
  await page.waitForTimeout(800);
  expect(await bgInk(page), '1字目のお手本').toBeGreaterThan(1000);

  for (const id of ['hira_i', 'hira_u']) {
    await page.click('[data-testid=btn-back]');
    await page.click(`[data-testid=char-${id}]`);
    await page.waitForSelector('[data-testid=practice-canvas] canvas');
    await page.waitForTimeout(800);
    expect(await bgInk(page), `${id} のお手本`).toBeGreaterThan(1000);
  }

  // 同じ字に入り直しても消えない (「もういっかい」相当)
  await page.click('[data-testid=btn-back]');
  await page.click('[data-testid=char-hira_u]');
  await page.waitForSelector('[data-testid=practice-canvas] canvas');
  await page.waitForTimeout(800);
  expect(await bgInk(page), '入り直したときのお手本').toBeGreaterThan(1000);
});

test('運筆のお手本は絵文字ではなく書く線そのもの', async ({ page }) => {
  await page.goto('/');
  await page.click('[data-testid=tile-unpitsu]');
  // かいだん: 文字コードは 🪜 (絵文字)。お手本フォントに無いので
  // フォント描画すると絵文字が出るか、何も出ない
  await page.click('[data-testid=char-unpitsu_kaidan]');
  await page.waitForSelector('[data-testid=practice-canvas] canvas');
  await page.waitForTimeout(800);
  expect(await bgInk(page), 'かいだんのお手本').toBeGreaterThan(1000);
  // 背景層に色が付いていない = 絵文字が描かれていない (お手本は無彩色のみ)
  const colored = await page.evaluate(() => {
    const c = document.querySelector(
      '[data-testid=practice-canvas] canvas',
    ) as HTMLCanvasElement;
    const d = c.getContext('2d')!.getImageData(0, 0, c.width, c.height).data;
    let n = 0;
    for (let i = 0; i < d.length; i += 4) {
      // 薄い画素は輪郭の平滑化。低アルファでは色が量子化されて
      // わずかに色付くので、目に見える濃さ (α>64) だけを数える
      if (d[i + 3] <= 64) continue;
      const max = Math.max(d[i], d[i + 1], d[i + 2]);
      const min = Math.min(d[i], d[i + 1], d[i + 2]);
      if (max - min > 24) n++; // 彩度のある画素
    }
    return n;
  });
  expect(colored, '背景層の有彩色画素 (絵文字が描かれた印)').toBe(0);
});
