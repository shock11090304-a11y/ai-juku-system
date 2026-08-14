// =============================================================================
// 冊子受験画面 — 手書きデータの往復検査 (生成側)
//
//   node scripts/book_exam/roundtrip_strokes.mjs
//
// ★ 何をしているか
//   exam-book-model.mjs を **実物のまま** import し、意地の悪い入力を通して
//   「クライアントが実際に送る JSON」を作って JSONL で吐く。
//   受け側 (scripts/book_exam/check_book_exam.py) が、使い捨ての Postgres の
//   strokes_are_valid() に食わせて突き合わせる。
//
// ★ 何を保証したいか
//     クライアントが送れるもの ⊆ DB が受け取るもの
//   これが崩れると「画面では保存したつもりなのに DB に拒否される」= 書き込みの消失。
//   逆に、モデルが弾いたものが DB を通ってしまうのは (今回の設計では) 許容する。
//   送らないので実害が無く、DB 側を厳しくするのは別の migration の仕事。
//
// ★ モデルの関数を写経しないこと。写経した瞬間、本物が壊れても検査が緑になる。
// =============================================================================
import {
  toNorm, OUT, thin, validateStrokes, parseStrokes, strokeHit, mergeAppend,
  createPageModel, pushStroke, eraseStrokes, undo, redo, PENS, MAX_STROKES, STROKE_V,
} from '../../exam-book-model.mjs';

const rect = { left: 100, top: 50, width: 800, height: 1131 };

/** toNorm を実際に通して点列を作る (モデルの入口を迂回しない) */
function trace(pts) {
  const out = [];
  for (const [cx, cy] of pts) {
    const n = toNorm(cx, cy, rect);
    if (n === OUT || n === null) continue;   // 画面側と同じ扱い: 捨てる / 切る
    out.push(n);
  }
  return out;
}

const cases = [];
const add = (name, strokes, note) => cases.push({ name, note, ...validateStrokes(strokes) });

// --- 正常系 -------------------------------------------------------------------
add('普通に1本引く',
  [{ ...PENS.normal, p: trace([[300, 400], [320, 420], [340, 445], [360, 470]]) }]);

add('マーカー (太い線・上限 0.1 未満)',
  [{ ...PENS.marker, p: trace([[150, 200], [700, 210]]) }]);

add('点を1つだけ (タップ)',
  [{ ...PENS.normal, p: trace([[500, 600]]) }]);

add('枠の四隅ちょうど',
  [{ ...PENS.thin, p: trace([[100, 50], [900, 50], [900, 1181], [100, 1181]]) }]);

add('間引きを通した長い線',
  [{ ...PENS.normal, p: thin(trace(Array.from({ length: 600 }, (_, i) =>
      [100 + (i * 800) / 600, 50 + Math.sin(i / 9) * 400 + 500]))) }]);

// --- モデルが捨てるべきもの (送信物に出てはいけない) ---------------------------
add('枠の外へドラッグ (OUT で切れる)',
  [{ ...PENS.normal, p: trace([[300, 400], [5000, 400], [320, 420]]) }],
  '枠外の点だけが落ち、残りは保存される');

add('幅0の枠で書いた (0除算)',
  [{ ...PENS.normal, p: [[300, 400], [320, 420]].map(([x, y]) =>
      toNorm(x, y, { left: 0, top: 0, width: 0, height: 0 })).filter((v) => Array.isArray(v)) }],
  'toNorm が null を返し点が全部消える → 0点ストロークとして落ちる');

add('NaN 座標',
  [{ ...PENS.normal, p: trace([[NaN, 400], [320, Infinity], [340, 445]]) }]);

add('c が無い (キー欠落)',      [{ w: 0.003, p: [[0.5, 0.5]] }]);
add('w が無い (キー欠落)',      [{ c: '#000', p: [[0.5, 0.5]] }]);
add('p が無い (キー欠落)',      [{ c: '#000', w: 0.003 }]);
add('c が undefined',           [{ c: undefined, w: 0.003, p: [[0.5, 0.5]] }]);
add('w が 0',                   [{ c: '#000', w: 0, p: [[0.5, 0.5]] }]);
add('w が負',                   [{ c: '#000', w: -0.003, p: [[0.5, 0.5]] }]);
add('w が上限超え (0.2)',       [{ c: '#000', w: 0.2, p: [[0.5, 0.5]] }]);
add('p が空配列',               [{ c: '#000', w: 0.003, p: [] }]);
add('点が3要素 (筆圧付き)',     [{ c: '#000', w: 0.003, p: [[0.3, 0.4, 0.7]] }]);
add('点が1要素',                [{ c: '#000', w: 0.003, p: [[0.3]] }]);
add('点が文字列',               [{ c: '#000', w: 0.003, p: ['0.3,0.4'] }]);
add('座標がピクセル値',         [{ c: '#000', w: 0.003, p: [[387, 798]] }]);
add('座標が負',                 [{ c: '#000', w: 0.003, p: [[-0.01, 0.5]] }]);
add('ストロークが null',        [null]);
add('ストロークが文字列',       ['線']);
add('壊れた1本と正常な1本が混在',
  [{ c: '#000', w: 0.003, p: [[387, 798]] }, { ...PENS.normal, p: [[0.5, 0.5], [0.6, 0.6]] }],
  '壊れた方だけ落ち、正常な方は残る');

// --- 上限 ---------------------------------------------------------------------
add('上限ちょうど',
  Array.from({ length: MAX_STROKES }, () => ({ ...PENS.thin, p: [[0.5, 0.5]] })));
add('上限超え',
  Array.from({ length: MAX_STROKES + 1 }, () => ({ ...PENS.thin, p: [[0.5, 0.5]] })));

// --- 編集操作を通した後の状態 -------------------------------------------------
{
  const m = createPageModel();
  pushStroke(m, { ...PENS.normal, p: trace([[200, 300], [260, 360]]) });
  pushStroke(m, { ...PENS.red,    p: trace([[400, 500], [460, 560]]) });
  pushStroke(m, { ...PENS.bold,   p: trace([[600, 700], [660, 760]]) });
  const hit = m.strokes.map((s, i) => (strokeHit(s, ...toNorm(430, 530, rect), 0.03) ? i : -1))
                       .filter((i) => i >= 0);
  eraseStrokes(m, hit);
  add('消しゴムで1本消した後', m.strokes, `消えた本数=${hit.length}`);
  undo(m);
  add('消しゴムを undo した後', m.strokes);
  redo(m);
  add('redo した後', m.strokes);
}

// --- 読み込み側 ---------------------------------------------------------------
const readback = [
  ['正常な保存物を読み直す', { v: 1, strokes: [{ c: '#000', w: 0.003, p: [[0.5, 0.5]] }] }],
  ['旧形式 (裸の配列)',      [{ points: [[10, 10]], color: '#000' }]],
  ['v が文字列 "1"',         { v: '1', strokes: [{ c: '#000', w: 0.003, p: [[0.5, 0.5]] }] }],
  ['v が 2',                 { v: 2, strokes: [] }],
  ['strokes キーが無い',     { v: 1 }],
  ['壊れた1本が混ざる',      { v: 1, strokes: [{}, { c: '#000', w: 0.003, p: [[0.5, 0.5]] }] }],
].map(([name, raw]) => {
  const r = parseStrokes(raw);
  return { kind: 'read', name, ok: r.ok, legacy: r.legacy, count: r.strokes.length };
});

// --- マージ -------------------------------------------------------------------
const a = [{ c: '#000', w: 0.003, p: [[0.1, 0.1]] }];
const b = [{ c: '#000', w: 0.003, p: [[0.1, 0.1]] }, { c: '#d02a2a', w: 0.003, p: [[0.2, 0.2]] }];
const merged = mergeAppend(a, b);
readback.push({ kind: 'merge', name: '2端末の追記マージ (同一ストロークは1本に)',
                ok: true, count: merged.length });

// --- 出力 ---------------------------------------------------------------------
for (const c of cases) {
  process.stdout.write(JSON.stringify({
    kind: 'write', name: c.name, note: c.note || null,
    clientOk: c.ok, dropped: c.dropped, reason: c.reason,
    strokeCount: c.payload ? c.payload.strokes.length : 0,
    payload: c.payload,
  }) + '\n');
}
for (const r of readback) process.stdout.write(JSON.stringify(r) + '\n');
process.stdout.write(JSON.stringify({ kind: 'meta', strokeV: STROKE_V, maxStrokes: MAX_STROKES }) + '\n');
