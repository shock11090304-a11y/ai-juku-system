// =============================================================================
// 冊子受験画面 — PDF の描画
//
// ★ 座標系の持ち主は `.page` ただ 1 つ。canvas は `.page` を 100% で満たすだけで、
//   個別の transform もスクロール補正も持たない。ここを崩すと手書きがずれる。
// =============================================================================
import * as pdfjsLib from '/vendor/pdfjs/pdf.min.mjs?v=6.2.108';

pdfjsLib.GlobalWorkerOptions.workerSrc = '/vendor/pdfjs/pdf.worker.min.mjs?v=6.2.108';

/** 1 枚の canvas の面積上限。iPad Safari は大きすぎる canvas を黙って捨てる。 */
const MAX_CANVAS_AREA = 12_000_000;

/** 表示倍率の段階。連続ズームは実装しない (ネイティブピンチと二重仕様になるため)。 */
export const ZOOM_STEPS = [1, 1.5, 2, 3];

export class Book {
  constructor() {
    this.doc = null;
    this.pages = [];        // [{n, w, h}] scale=1 での実寸
    this.zoom = 1;
    this._tasks = new Map();
  }

  /**
   * PDF を取得して開く。
   * ★ 署名付き URL を getDocument に直接渡さない。Range 遅延取得だと 60 分超の
   *   模試の途中で署名が切れ、まだ見ていないページが開けなくなる。先に全部落とす。
   */
  async open(signedUrl, onProgress) {
    const res = await fetch(signedUrl);
    if (!res.ok) throw new Error(`冊子を取得できません (HTTP ${res.status})`);
    const total = Number(res.headers.get('Content-Length') || 0);
    const reader = res.body && res.body.getReader ? res.body.getReader() : null;
    let buf;
    if (reader) {
      const chunks = []; let got = 0;
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        chunks.push(value); got += value.length;
        if (onProgress) onProgress(total ? got / total : 0, got, total);
      }
      buf = new Uint8Array(got);
      let off = 0;
      for (const c of chunks) { buf.set(c, off); off += c.length; }
    } else {
      buf = new Uint8Array(await res.arrayBuffer());
    }

    this.doc = await pdfjsLib.getDocument({
      data: buf.slice(0),                    // worker に transfer されて detach するので複製
      cMapUrl: '/vendor/pdfjs/cmaps/', cMapPacked: true,
      standardFontDataUrl: '/vendor/pdfjs/standard_fonts/',
      isEvalSupported: false,
    }).promise;

    // ★ 全ページの実寸を **先に** 取る。仮寸でページ枠を作ると、実寸が決まった瞬間に
    //   「インクだけ縦に伸びる」。受験を始める前にここまで終わらせる。
    this.pages = [];
    for (let n = 1; n <= this.doc.numPages; n++) {
      const vp = (await this.doc.getPage(n)).getViewport({ scale: 1 });
      this.pages.push({ n, w: vp.width, h: vp.height });
    }
    return this.pages.length;
  }

  /** ページ枠を作る。aspect-ratio に実寸を入れるので、描画前でも高さが確定する。 */
  buildPageElements(host) {
    host.innerHTML = '';
    return this.pages.map((p) => {
      const el = document.createElement('div');
      el.className = 'page';
      el.dataset.page = String(p.n);
      el.style.aspectRatio = `${p.w} / ${p.h}`;
      el.innerHTML =
        '<canvas class="lyr pdf"></canvas>' +
        '<canvas class="lyr dry"></canvas>' +
        '<canvas class="lyr wet"></canvas>' +
        '<div class="pageno"></div>';
      el.querySelector('.pageno').textContent = String(p.n);
      host.appendChild(el);
      return el;
    });
  }

  /** そのページを今の表示幅で描く。★同じページの描画が重なったら前のをキャンセルする。 */
  async render(pageEl) {
    const n = Number(pageEl.dataset.page);
    const cv = pageEl.querySelector('canvas.pdf');
    const cssW = pageEl.clientWidth;
    if (!(cssW > 0)) return;

    const dpr = Math.min(window.devicePixelRatio || 1, 3);
    const meta = this.pages[n - 1];
    let scale = (cssW * dpr) / meta.w;
    // 面積上限。超えたら解像度を落とす (描かれないより荒い方がまし)
    const area = meta.w * scale * meta.h * scale;
    if (area > MAX_CANVAS_AREA) scale *= Math.sqrt(MAX_CANVAS_AREA / area);

    const prev = this._tasks.get(n);
    if (prev) { try { prev.cancel(); } catch (_) {} }

    const page = await this.doc.getPage(n);
    const vp = page.getViewport({ scale });
    cv.width = Math.max(1, Math.floor(vp.width));
    cv.height = Math.max(1, Math.floor(vp.height));
    const task = page.render({ canvasContext: cv.getContext('2d', { alpha: false }),
                               viewport: vp, canvas: cv });
    this._tasks.set(n, task);
    try {
      await task.promise;
    } catch (e) {
      if (e && e.name === 'RenderingCancelledException') return;
      throw e;
    } finally {
      if (this._tasks.get(n) === task) this._tasks.delete(n);
    }
  }
}

/** Storage から署名付き URL を取る (1 時間有効)。 */
export async function signedUrl(sbClient, path) {
  const { data, error } = await sbClient.storage.from('book-pdfs').createSignedUrl(path, 3600);
  if (error) throw new Error(`冊子の URL を取得できません: ${error.message}`);
  return data.signedUrl;
}
