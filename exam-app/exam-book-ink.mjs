// =============================================================================
// 冊子受験画面 — 手書き層
//
// ★ 入力の振り分けがこの画面のいちばんの難所。iPad を普通に持って書くと
//   手のひらが先に触れる。1 本指タッチで**何も起こさない**ようにして初めて
//   「紙を押さえて書く」ができる。移動は 2 本指。
//
// ★ 座標は toNorm を通したものだけを持つ。画面のピクセルはモデルに入れない。
// =============================================================================
import {
  toNorm, OUT, thin, strokeHit, PENS, MAX_STROKES,
  createPageModel, pushStroke, eraseStrokes, undo, redo,
} from '/exam-book-model.mjs?v=1';

export const MODE = Object.freeze({ READ: 'read', WRITE: 'write' });
const ERASER_R = 0.012;          // 消しゴムの当たり半径 (ページ幅比)

export class Ink {
  /**
   * @param {HTMLElement} viewer スクロールする箱
   * @param {(page:number)=>void} onDirty そのページに変更が入った (保存キューへ)
   * @param {(page:number)=>void} onLimit 上限に達して書けなかった
   *   ★ 黙って捨てない。生徒は書けたつもりでいるので、必ず画面に出す。
   */
  constructor(viewer, onDirty, onLimit = () => {}) {
    this.viewer = viewer;
    this.onDirty = onDirty;
    this.onLimit = onLimit;
    this.models = new Map();       // page -> model
    this.ready = new Set();        // ★読み込みが終わったページだけ書ける (F6)
    this.mode = MODE.READ;
    this.pen = PENS.normal;
    this.eraser = false;
    this._cur = null;              // 描いている最中のストローク
    this._curPage = null;
    this._pending = [];            // まだ push していない点 (0 点ストロークを作らない)
    this._rects = new Map();       // page -> DOMRect (ResizeObserver で無効化)
    this._pointers = new Map();
    this._panFrom = null;
    viewer.dataset.mode = this.mode;   // CSS の touch-action がこれを見る

    viewer.addEventListener('pointerdown', (e) => this._down(e), { passive: false });
    viewer.addEventListener('pointermove', (e) => this._move(e), { passive: false });
    for (const t of ['pointerup', 'pointercancel', 'pointerleave', 'lostpointercapture']) {
      viewer.addEventListener(t, (e) => this._up(e), { passive: false });
    }
    // ★ スクロールすると getBoundingClientRect は全ページ変わる (ビューポート基準)。
    //   リサイズと DPR は無効化していたのに、スクロールが漏れていた。
    //   実機 (iPad) で「書く → スクロール → 書く」の 2 本目が
    //   スクロール量ぶんずれて記録された (2026-08-15)。
    viewer.addEventListener('scroll', () => this._rects.clear(), { passive: true });
  }

  setMode(m) {
    this.mode = m;
    this.viewer.dataset.mode = m;
    this._abort();
  }
  setPen(p) { this.pen = p; this.eraser = false; }
  setEraser(on) { this.eraser = !!on; }

  model(page) {
    if (!this.models.has(page)) this.models.set(page, createPageModel());
    return this.models.get(page);
  }

  /** DB から読んだものを入れる。★ここを通ったページだけが書き込み可になる。 */
  loadPage(page, strokes) {
    this.model(page).strokes = strokes || [];
    this.ready.add(page);
    this.redraw(page);
  }
  markUnavailable(page) { this.ready.delete(page); }

  invalidateRect(page) { this._rects.delete(page); }

  _pageEl(page) { return this.viewer.querySelector(`.page[data-page="${page}"]`); }

  _rect(page) {
    if (!this._rects.has(page)) {
      const el = this._pageEl(page);
      if (!el) return null;
      this._rects.set(page, el.getBoundingClientRect());
    }
    return this._rects.get(page);
  }

  _pageAt(e) {
    const el = e.target && e.target.closest ? e.target.closest('.page') : null;
    return el ? Number(el.dataset.page) : null;
  }

  // --- 入力の振り分け ---------------------------------------------------------
  _down(e) {
    this._pointers.set(e.pointerId, e);

    if (this.mode !== MODE.WRITE) return;             // 読むモードは素通り (ネイティブピンチ)

    // 2 本目が来たら、書きかけを捨てて 2 本指パンへ切り替える
    if (this._pointers.size >= 2) {
      this._abort();
      const pts = [...this._pointers.values()];
      this._panFrom = { x: (pts[0].clientX + pts[1].clientX) / 2,
                        y: (pts[0].clientY + pts[1].clientY) / 2,
                        sl: this.viewer.scrollLeft, st: this.viewer.scrollTop };
      return;
    }

    // ★ 1 本指の touch は **何も起こさない**。手のひらで紙を押さえられるようにする。
    //   ペン (pen) とマウスだけが描ける。
    if (e.pointerType === 'touch') { e.preventDefault(); return; }

    const page = this._pageAt(e);
    if (page == null || !this.ready.has(page)) return;   // 未読込のページには書かせない

    // ★ 線の始まりでは必ず測り直す。キャッシュが効くのは 1 ストロークの中だけ
    //   (ストローク中は preventDefault しているのでページは動かない)。
    //   これでキャッシュの古さがどこから来ても 1 ストロークを跨げない。
    this._rects.delete(page);

    e.preventDefault();
    // 既に離されたポインタを掴もうとすると NotFoundError。掴めなくても描画は続けられる。
    try { this.viewer.setPointerCapture(e.pointerId); } catch (_) {}
    this._curPage = page;

    // Apple Pencil の反対側 (e.buttons===32) は消しゴム扱いにしない。
    // 誤爆が多く、切り替えたことに気づけないため。ツールバーで明示的に選ぶ。
    if (this.eraser) { this._eraseAt(e); return; }

    this._cur = { c: this.pen.c, w: this.pen.w, p: [] };
    this._pending = [];
    this._addPoint(e);
  }

  _move(e) {
    if (this._pointers.has(e.pointerId)) this._pointers.set(e.pointerId, e);

    if (this.mode !== MODE.WRITE) return;

    if (this._panFrom && this._pointers.size >= 2) {
      const pts = [...this._pointers.values()];
      const cx = (pts[0].clientX + pts[1].clientX) / 2;
      const cy = (pts[0].clientY + pts[1].clientY) / 2;
      this.viewer.scrollLeft = this._panFrom.sl - (cx - this._panFrom.x);
      this.viewer.scrollTop = this._panFrom.st - (cy - this._panFrom.y);
      e.preventDefault();
      return;
    }

    if (this._curPage == null) return;
    if (this.eraser) { this._eraseAt(e); e.preventDefault(); return; }
    if (!this._cur) return;

    e.preventDefault();
    // coalesced があれば取りこぼしを拾う (無い環境もあるのでガード)
    const evs = (typeof e.getCoalescedEvents === 'function' && e.getCoalescedEvents().length)
      ? e.getCoalescedEvents() : [e];
    for (const ev of evs) this._addPoint(ev);
    this._drawWet();
  }

  _up(e) {
    this._pointers.delete(e.pointerId);
    if (this._panFrom && this._pointers.size < 2) this._panFrom = null;
    if (this.mode !== MODE.WRITE) return;
    if (this._curPage == null) return;

    const page = this._curPage;
    this._commitStroke(page);
    this._cur = null;
    this._curPage = null;
    this._clearWet(page);
  }

  /** 書きかけを確定してモデルに積む。★ 上限判定はここ 1 箇所に集める。 */
  _commitStroke(page) {
    if (!this._cur || this._cur.p.length === 0) return false;
    this._cur.p = thin(this._cur.p);
    const m = this.model(page);
    if (m.strokes.length >= MAX_STROKES) {
      this.onLimit(page);            // ★ 捨てたことを必ず知らせる
      return false;
    }
    pushStroke(m, this._cur);
    this.redraw(page);
    this.onDirty(page);              // ★ pointerup で即キューへ (ローカル写しもここで)
    return true;
  }

  /** 書きかけを捨てる。pointercancel (電話着信・アプリ切替) でも必ず通る。 */
  _abort() {
    if (this._curPage != null) this._clearWet(this._curPage);
    this._cur = null;
    this._curPage = null;
  }

  _addPoint(e) {
    const rect = this._rect(this._curPage);
    const n = toNorm(e.clientX, e.clientY, rect);
    if (n === null) return;                       // 枠が測れない → 捨てる
    if (n === OUT) {                              // ★枠外では線を切る (clamp しない)
      this._commitStroke(this._curPage);
      this._cur = { c: this.pen.c, w: this.pen.w, p: [] };   // 戻ってきたら新しい線
      return;
    }
    this._cur.p.push(n);
  }

  _eraseAt(e) {
    const page = this._curPage;
    const rect = this._rect(page);
    const n = toNorm(e.clientX, e.clientY, rect);
    if (!Array.isArray(n)) return;
    const m = this.model(page);
    const hit = [];
    m.strokes.forEach((s, i) => { if (strokeHit(s, n[0], n[1], ERASER_R)) hit.push(i); });
    if (hit.length) {
      eraseStrokes(m, hit);
      this.redraw(page);
      this.onDirty(page);
    }
  }

  undo(page) { if (undo(this.model(page))) { this.redraw(page); this.onDirty(page); } }
  redo(page) { if (redo(this.model(page))) { this.redraw(page); this.onDirty(page); } }

  // --- 描画 -------------------------------------------------------------------
  _fit(cv, el) {
    const dpr = Math.min(window.devicePixelRatio || 1, 3);
    const w = Math.max(1, Math.round(el.clientWidth * dpr));
    const h = Math.max(1, Math.round(el.clientHeight * dpr));
    if (cv.width !== w || cv.height !== h) { cv.width = w; cv.height = h; }
    return cv.getContext('2d');
  }

  _strokePath(ctx, s, W, H) {
    ctx.strokeStyle = s.c;
    ctx.lineWidth = Math.max(1, s.w * W);
    ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    ctx.beginPath();
    const p = s.p;
    if (p.length === 1) {                       // 点は小さな丸で描く (線にならないため)
      ctx.arc(p[0][0] * W, p[0][1] * H, ctx.lineWidth / 2, 0, Math.PI * 2);
      ctx.fillStyle = s.c; ctx.fill(); return;
    }
    ctx.moveTo(p[0][0] * W, p[0][1] * H);
    for (let i = 1; i < p.length; i++) ctx.lineTo(p[i][0] * W, p[i][1] * H);
    ctx.stroke();
  }

  redraw(page) {
    const el = this._pageEl(page);
    if (!el) return;
    const cv = el.querySelector('canvas.dry');
    const ctx = this._fit(cv, el);
    ctx.clearRect(0, 0, cv.width, cv.height);
    for (const s of this.model(page).strokes) this._strokePath(ctx, s, cv.width, cv.height);
  }

  _drawWet() {
    const el = this._pageEl(this._curPage);
    if (!el || !this._cur) return;
    const cv = el.querySelector('canvas.wet');
    const ctx = this._fit(cv, el);
    ctx.clearRect(0, 0, cv.width, cv.height);
    this._strokePath(ctx, this._cur, cv.width, cv.height);
  }

  _clearWet(page) {
    const el = this._pageEl(page);
    if (!el) return;
    const cv = el.querySelector('canvas.wet');
    cv.getContext('2d').clearRect(0, 0, cv.width, cv.height);
  }
}
