// =============================================================================
// 冊子受験画面 — データモデル (純関数だけ)
//
// ★ このファイルは DOM も Supabase も触らない。
//   node からそのまま import できるので、ゲート (scripts/book_exam/) が
//   **実物を** 検査する。ブラウザでしか動かない書き方をしないこと。
//
// ★ 保存する形は設計書 §5 (supabase/migrations/…_strokes_format.sql が DB 側で強制):
//     {"v":1,"strokes":[{"c":"#1b2233","w":0.003,"p":[[0.3124,0.4551], …]}]}
//   座標 p も線幅 w も **ページの幅・高さを 1 とした正規化値**。
//   これで書いた端末と見る端末が違っても、拡大率が変わっても位置がずれない。
//
// ★ DB の CHECK より **こちらの方を厳しく**しておく。
//   DB 側は「キーが無い」を一度素通ししていた (2026-08-14 に修正済み) ように、
//   後から緩さが見つかることがある。壊れたものを送らないのがクライアントの責任。
// =============================================================================

/** 保存フォーマットの版。上げるときは DB 側の strokes_are_valid() も直す。 */
export const STROKE_V = 1;

/** 1 ページあたりのストローク数の上限 (DB の CHECK が 5000 で弾く)。
 *  手前で止めて「保存が丸ごと通らない」状態を作らない。 */
export const MAX_STROKES = 4800;

/** 座標の丸め桁。4 桁 = 幅 2000px のページで 0.2px 相当。これ以上は無駄。 */
const Q = 1e4;

/** ペンの太さ。★ページ幅に対する比。定数から選ばせて、下限割れ (w<=0) や
 *  上限超え (w>0.1) を構造的に起こせなくする。 */
export const PENS = Object.freeze({
  thin:   Object.freeze({ c: '#1b2233', w: 0.0018 }),
  normal: Object.freeze({ c: '#1b2233', w: 0.0030 }),
  bold:   Object.freeze({ c: '#1b2233', w: 0.0052 }),
  red:    Object.freeze({ c: '#d02a2a', w: 0.0030 }),
  marker: Object.freeze({ c: '#f5c518', w: 0.0180 }),
});

/** 枠外の点を表す番兵。★clamp しない。
 *  clamp すると枠の縁に線が張り付いて、書いていない線が残る。
 *  呼び出し側はここでストロークを切り、戻ってきたら新しいストロークを始める。 */
export const OUT = Symbol('out');

/** 枠のすぐ外までは「まだ枠内」として扱う余裕。ペン先が 1px はみ出しただけで
 *  線が切れると書き味が悪い。0〜1 に丸めて保存する。 */
const MARGIN = 0.02;

const clamp01 = (v) => (v < 0 ? 0 : v > 1 ? 1 : v);
const quant = (v) => Math.round(v * Q) / Q;

/**
 * 画面座標 → 正規化座標。**保存に入る唯一の入口。**
 * @returns {[number,number] | null | typeof OUT}
 *   null … 枠の大きさが取れない / 数値にならない (捨てる)
 *   OUT  … 枠の外 (ストロークを切る)
 */
export function toNorm(clientX, clientY, rect) {
  // ★ 0 除算を作らない。rect が 0 幅だと x が Infinity → JSON で null → DB が 23514 で
  //   弾き、そのページが永久に保存できなくなる。ボトムシートの開閉中などに実際に起きる。
  if (!rect) return null;
  const { left, top, width, height } = rect;
  if (!(width > 0) || !(height > 0)) return null;
  if (!Number.isFinite(clientX) || !Number.isFinite(clientY)) return null;

  const x = (clientX - left) / width;
  const y = (clientY - top) / height;
  if (!Number.isFinite(x) || !Number.isFinite(y)) return null;

  if (x < -MARGIN || x > 1 + MARGIN || y < -MARGIN || y > 1 + MARGIN) return OUT;
  return [quant(clamp01(x)), quant(clamp01(y))];
}

/**
 * 点の間引き。直前に残した点から minDist 未満の点は捨てる。
 * ★ 最後の点は必ず残す (残さないと線の終端が動く)。
 */
export function thin(points, minDist = 0.0015) {
  if (!Array.isArray(points) || points.length <= 2) return points ? points.slice() : [];
  const out = [points[0]];
  const d2 = minDist * minDist;
  for (let i = 1; i < points.length - 1; i++) {
    const [px, py] = out[out.length - 1];
    const [x, y] = points[i];
    const dx = x - px, dy = y - py;
    if (dx * dx + dy * dy >= d2) out.push(points[i]);
  }
  out.push(points[points.length - 1]);
  return out;
}

/** 点と線分の距離の 2 乗。消しゴムの当たり判定に使う。 */
function distToSegSq(px, py, ax, ay, bx, by) {
  const vx = bx - ax, vy = by - ay;
  const wx = px - ax, wy = py - ay;
  const vv = vx * vx + vy * vy;
  if (vv === 0) return wx * wx + wy * wy;
  let t = (wx * vx + wy * vy) / vv;
  t = t < 0 ? 0 : t > 1 ? 1 : t;
  const dx = px - (ax + t * vx), dy = py - (ay + t * vy);
  return dx * dx + dy * dy;
}

/**
 * 消しゴム。★ストローク単位で消す (§5 に部分消しの表現が無いため)。
 * @returns true = この点に触れている
 */
export function strokeHit(stroke, x, y, radius) {
  const p = stroke && stroke.p;
  if (!Array.isArray(p) || p.length === 0) return false;
  const r2 = radius * radius;
  if (p.length === 1) {
    const dx = x - p[0][0], dy = y - p[0][1];
    return dx * dx + dy * dy <= r2;
  }
  for (let i = 1; i < p.length; i++) {
    if (distToSegSq(x, y, p[i - 1][0], p[i - 1][1], p[i][0], p[i][1]) <= r2) return true;
  }
  return false;
}

/**
 * 送信直前のバリデータ。**DB の CHECK より厳しい。**
 * 通ったものだけを送る。壊れた 1 本のせいでページ全体が保存できなくなるのを防ぐ。
 *
 * ★ 送信オブジェクトは {c,w,p} を **明示的に組み直す**。
 *   モデル側に余計なキー (描画用のキャッシュなど) が付いていても混ぜない。
 *   また undefined のキーは JSON.stringify で消えるため、DB 側では
 *   「キーが無い」形になる。ここで存在と型を必ず見る。
 *
 * @returns {{ok:boolean, payload:object|null, dropped:number, reason:string|null}}
 */
export function validateStrokes(strokes) {
  if (!Array.isArray(strokes)) {
    return { ok: false, payload: null, dropped: 0, reason: 'strokes が配列でない' };
  }
  const out = [];
  let dropped = 0;

  for (const s of strokes) {
    if (!s || typeof s !== 'object') { dropped++; continue; }
    const { c, w, p } = s;

    if (typeof c !== 'string' || c.length === 0) { dropped++; continue; }
    if (typeof w !== 'number' || !Number.isFinite(w) || w <= 0 || w > 0.1) { dropped++; continue; }
    if (!Array.isArray(p) || p.length === 0) { dropped++; continue; }

    const pts = [];
    let bad = false;
    for (const pt of p) {
      if (!Array.isArray(pt) || pt.length !== 2) { bad = true; break; }
      const [x, y] = pt;
      if (typeof x !== 'number' || typeof y !== 'number') { bad = true; break; }
      if (!Number.isFinite(x) || !Number.isFinite(y)) { bad = true; break; }
      if (x < 0 || x > 1 || y < 0 || y > 1) { bad = true; break; }
      pts.push([quant(x), quant(y)]);
    }
    if (bad || pts.length === 0) { dropped++; continue; }

    out.push({ c, w, p: pts });
  }

  if (out.length > MAX_STROKES) {
    return {
      ok: false, payload: null, dropped,
      reason: `ストロークが ${out.length} 本 (上限 ${MAX_STROKES})`,
    };
  }
  return { ok: true, payload: { v: STROKE_V, strokes: out }, dropped, reason: null };
}

/**
 * 読み込み側。DB から来た jsonb をモデルに戻す。
 * ★ 版は String() で比べる。数値の 1 と文字列の "1" のどちらで入っていても読めるように
 *   (書くのは常に数値。古い行や他実装が書いたものを読み捨てないため)。
 * @returns {{ok:boolean, strokes:Array, legacy:boolean}}
 */
export function parseStrokes(raw) {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) {
    // 裸の配列 = §5 を決める前の旧形式。座標の基準が無いので復元できない。
    return { ok: false, strokes: [], legacy: Array.isArray(raw) };
  }
  if (String(raw.v) !== String(STROKE_V)) return { ok: false, strokes: [], legacy: true };
  if (!Array.isArray(raw.strokes)) return { ok: false, strokes: [], legacy: false };

  // 読むときも素通しにしない。壊れた 1 本を描画に回すと例外で画面全体が止まる。
  const v = validateStrokes(raw.strokes);
  return { ok: true, strokes: v.payload ? v.payload.strokes : [], legacy: false };
}

/**
 * 2 端末で同じページを触ったときの追記マージ。
 * ★ 消しゴムを使っていない限り「両方残す」が安全側。消えるより増える方がまし。
 *   同じストローク (色・太さ・点列が完全一致) は 1 本にまとめる。
 */
export function mergeAppend(mine, theirs) {
  const key = (s) => s.c + '|' + s.w + '|' + s.p.map((q) => q[0] + ',' + q[1]).join(';');
  const seen = new Set();
  const out = [];
  for (const s of [...(theirs || []), ...(mine || [])]) {
    const k = key(s);
    if (seen.has(k)) continue;
    seen.add(k);
    out.push(s);
  }
  return out;
}

/** ページごとのモデル。undo/redo はメモリ上だけ (DB は最新状態しか持てない)。 */
export function createPageModel() {
  return { strokes: [], undo: [], redo: [] };
}

export function pushStroke(model, stroke) {
  model.strokes.push(stroke);
  model.undo.push({ type: 'add', index: model.strokes.length - 1, stroke });
  model.redo.length = 0;
  return model;
}

export function eraseStrokes(model, indexes) {
  const sorted = [...indexes].sort((a, b) => b - a);
  const removed = [];
  for (const i of sorted) {
    if (i >= 0 && i < model.strokes.length) removed.push({ index: i, stroke: model.strokes[i] });
  }
  if (removed.length === 0) return model;
  for (const r of removed) model.strokes.splice(r.index, 1);
  model.undo.push({ type: 'erase', removed });
  model.redo.length = 0;
  return model;
}

export function undo(model) {
  const op = model.undo.pop();
  if (!op) return false;
  if (op.type === 'add') {
    model.strokes.splice(op.index, 1);
  } else {
    for (const r of [...op.removed].sort((a, b) => a.index - b.index)) {
      model.strokes.splice(r.index, 0, r.stroke);
    }
  }
  model.redo.push(op);
  return true;
}

export function redo(model) {
  const op = model.redo.pop();
  if (!op) return false;
  if (op.type === 'add') {
    model.strokes.splice(op.index, 0, op.stroke);
  } else {
    for (const r of [...op.removed].sort((a, b) => b.index - a.index)) {
      model.strokes.splice(r.index, 1);
    }
  }
  model.undo.push(op);
  return true;
}
