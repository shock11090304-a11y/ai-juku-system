/**
 * ストロークデータ作成用の開発者ツール (§4.4 方法A)。
 * 背景に参照用の文字を薄く表示し、クリックで制御点を打って JSON を出力する。
 * プレビューは実アプリと同じスプライン (engine/geometry) を使う。
 */
import { splineSample } from '../../src/engine/geometry';
import type { Pt, RawCharacterDef, RawStroke, StrokeEnding, StrokeHint } from '../../src/engine/types';

const SIZE = 512;
const COLORS = ['#e05d5d', '#3b82f6', '#22a559', '#e08a1e', '#8b5cf6', '#0ea5b0'];

const cv = document.getElementById('cv') as HTMLCanvasElement;
const ctx = cv.getContext('2d')!;

type EditStroke = { points: Pt[]; hint: StrokeHint; ending: StrokeEnding };

let strokes: EditStroke[] = [];
let current: Pt[] = [];
let selected = -1; // 確定済みの画を選択して再編集するとき
let dragging: { stroke: number; pt: number } | null = null; // stroke -1 = current

const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const charInput = $<HTMLInputElement>('m-char');

function pointsOf(i: number): Pt[] {
  return i === -1 ? current : strokes[i].points;
}

function draw() {
  ctx.clearRect(0, 0, SIZE, SIZE);
  // マス目
  ctx.strokeStyle = '#cfd8dc';
  ctx.setLineDash([8, 8]);
  ctx.beginPath();
  ctx.moveTo(SIZE / 2, 0);
  ctx.lineTo(SIZE / 2, SIZE);
  ctx.moveTo(0, SIZE / 2);
  ctx.lineTo(SIZE, SIZE / 2);
  ctx.stroke();
  ctx.setLineDash([]);
  // 参照文字（下敷き）
  if (charInput.value) {
    ctx.save();
    ctx.globalAlpha = 0.13;
    ctx.font = `${SIZE * 0.9}px IPAGothic, 'Hiragino Sans', sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = '#000';
    ctx.fillText(charInput.value, SIZE / 2, SIZE / 2 + SIZE * 0.04);
    ctx.restore();
  }
  // 画
  const all = [...strokes.map((s) => s.points), ...(current.length ? [current] : [])];
  all.forEach((pts, i) => {
    if (pts.length === 0) return;
    const color = COLORS[i % COLORS.length];
    if (pts.length >= 2) {
      const dense = splineSample(pts, 32);
      ctx.strokeStyle = color;
      ctx.globalAlpha = i === selected ? 0.9 : 0.5;
      ctx.lineWidth = SIZE * 0.11;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      ctx.beginPath();
      dense.forEach((p, k) =>
        k === 0 ? ctx.moveTo(p.x * SIZE, p.y * SIZE) : ctx.lineTo(p.x * SIZE, p.y * SIZE),
      );
      ctx.stroke();
      ctx.globalAlpha = 1;
    }
    // 制御点
    for (const p of pts) {
      ctx.fillStyle = '#fff';
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(p.x * SIZE, p.y * SIZE, 5, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
    }
    // 始点と番号
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(pts[0].x * SIZE, pts[0].y * SIZE, 9, 0, Math.PI * 2);
    ctx.fill();
    ctx.font = 'bold 22px sans-serif';
    ctx.fillText(String(i + 1), pts[0].x * SIZE + 14, pts[0].y * SIZE - 8);
  });
  renderStrokeList();
}

function renderStrokeList() {
  const el = $('strokes');
  el.innerHTML = '';
  strokes.forEach((s, i) => {
    const row = document.createElement('div');
    row.className = 'stroke-row' + (i === selected ? ' active' : '');
    row.innerHTML = `<b style="color:${COLORS[i % COLORS.length]}">${i + 1}画</b> ${
      s.points.length
    }点 ${s.hint}/${s.ending}`;
    const edit = document.createElement('button');
    edit.textContent = '選択';
    edit.onclick = () => {
      selected = selected === i ? -1 : i;
      draw();
    };
    const del = document.createElement('button');
    del.textContent = '削除';
    del.onclick = () => {
      strokes.splice(i, 1);
      selected = -1;
      draw();
    };
    row.append(' ', edit, del);
    el.append(row);
  });
}

function toNorm(e: MouseEvent): Pt {
  const r = cv.getBoundingClientRect();
  return {
    x: Math.round(((e.clientX - r.left) / r.width) * 100) / 100,
    y: Math.round(((e.clientY - r.top) / r.height) * 100) / 100,
  };
}

function hitPoint(p: Pt): { stroke: number; pt: number } | null {
  const R = 12 / SIZE;
  const targets = selected >= 0 ? [selected] : [-1];
  for (const t of targets) {
    const pts = pointsOf(t);
    for (let i = 0; i < pts.length; i++) {
      if (Math.hypot(pts[i].x - p.x, pts[i].y - p.y) < R) return { stroke: t, pt: i };
    }
  }
  return null;
}

cv.addEventListener('pointerdown', (e) => {
  const p = toNorm(e);
  if (e.button === 2) return; // 右クリックは contextmenu で
  const hit = hitPoint(p);
  if (hit) {
    dragging = hit;
  } else {
    (selected >= 0 ? strokes[selected].points : current).push(p);
    draw();
  }
});
cv.addEventListener('pointermove', (e) => {
  if (!dragging) return;
  const p = toNorm(e);
  pointsOf(dragging.stroke)[dragging.pt] = p;
  draw();
});
window.addEventListener('pointerup', () => (dragging = null));
cv.addEventListener('contextmenu', (e) => {
  e.preventDefault();
  const hit = hitPoint(toNorm(e));
  if (hit) {
    pointsOf(hit.stroke).splice(hit.pt, 1);
    draw();
  }
});

$('commit').onclick = () => {
  if (selected >= 0) {
    selected = -1;
    draw();
    return;
  }
  if (current.length < 2) return alert('制御点は2つ以上必要です');
  strokes.push({
    points: current,
    hint: $<HTMLSelectElement>('s-hint').value as StrokeHint,
    ending: $<HTMLSelectElement>('s-ending').value as StrokeEnding,
  });
  current = [];
  draw();
};
$('undo-pt').onclick = () => {
  (selected >= 0 ? strokes[selected].points : current).pop();
  draw();
};
$('clear').onclick = () => {
  if (!confirm('全部消しますか？')) return;
  strokes = [];
  current = [];
  selected = -1;
  draw();
};

function buildJson(): RawCharacterDef {
  const rawStrokes: RawStroke[] = strokes.map((s, i) => ({
    index: i + 1,
    hint: s.hint,
    ending: s.ending,
    points: s.points.map((p) => [p.x, p.y] as [number, number]),
  }));
  return {
    id: $<HTMLInputElement>('m-id').value,
    char: charInput.value,
    reading: $<HTMLInputElement>('m-reading').value || charInput.value,
    type: $<HTMLSelectElement>('m-type').value as RawCharacterDef['type'],
    group: $<HTMLInputElement>('m-group').value,
    strokes: rawStrokes,
  };
}

$('copy').onclick = async () => {
  const json = JSON.stringify(buildJson(), null, 2);
  $<HTMLTextAreaElement>('json').value = json;
  try {
    await navigator.clipboard.writeText(json);
  } catch {
    $<HTMLTextAreaElement>('json').select();
  }
};

$('load').onclick = () => {
  try {
    const def = JSON.parse($<HTMLTextAreaElement>('json').value) as RawCharacterDef;
    $<HTMLInputElement>('m-id').value = def.id ?? '';
    charInput.value = def.char ?? '';
    $<HTMLInputElement>('m-reading').value = def.reading ?? '';
    $<HTMLSelectElement>('m-type').value = def.type ?? 'hiragana';
    $<HTMLInputElement>('m-group').value = def.group ?? '';
    strokes = (def.strokes ?? []).map((s) => ({
      points: s.points.map(([x, y]) => ({ x, y })),
      hint: s.hint,
      ending: s.ending ?? 'tome',
    }));
    current = [];
    selected = -1;
    draw();
  } catch (err) {
    alert(`JSON が読めません: ${String(err)}`);
  }
};

charInput.addEventListener('input', draw);
draw();
