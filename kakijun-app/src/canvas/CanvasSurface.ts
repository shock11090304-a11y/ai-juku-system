/**
 * DPR 対応・リサイズ・座標変換 (§5.1, §5.2, §12.3)。
 * Canvas を3枚重ねる: 背景層 / ガイド層 / インク層。
 * 判定エンジンへは必ず正規化座標 (0〜1) を渡す。変換はこのクラスの責務。
 */
import type { Pt } from '../engine/types';

export class CanvasSurface {
  readonly container: HTMLElement;
  readonly bg: HTMLCanvasElement;
  readonly guide: HTMLCanvasElement;
  readonly ink: HTMLCanvasElement;
  readonly bgCtx: CanvasRenderingContext2D;
  readonly guideCtx: CanvasRenderingContext2D;
  readonly inkCtx: CanvasRenderingContext2D;
  /** CSS ピクセルでの1辺 S。描画エリアは必ず正方形 (§5.2) */
  size = 0;
  /** サイズ確定後・変更後に呼ばれる。全レイヤーの再描画をここで行うこと (§12.3) */
  onLayout: ((size: number) => void) | null = null;

  private ro: ResizeObserver;
  private orientationHandler: () => void;

  constructor(container: HTMLElement) {
    this.container = container;
    const make = (z: number) => {
      const c = document.createElement('canvas');
      c.style.position = 'absolute';
      c.style.inset = '0';
      c.style.zIndex = String(z);
      c.style.width = '100%';
      c.style.height = '100%';
      container.appendChild(c);
      return c;
    };
    this.bg = make(1);
    this.guide = make(2);
    this.ink = make(3);
    this.bgCtx = this.bg.getContext('2d')!;
    this.guideCtx = this.guide.getContext('2d')!;
    this.inkCtx = this.ink.getContext('2d')!;

    this.ro = new ResizeObserver(() => this.layout());
    this.ro.observe(container);
    // ResizeObserver が拾わないケースの保険 (§12.3)
    this.orientationHandler = () => setTimeout(() => this.layout(), 50);
    window.addEventListener('orientationchange', this.orientationHandler);
    this.layout();
  }

  layout(): void {
    const rect = this.container.getBoundingClientRect();
    const S = Math.floor(Math.min(rect.width, rect.height));
    if (S <= 0) return;
    const dpr = window.devicePixelRatio || 1;
    const px = Math.round(S * dpr);
    const changed = S !== this.size || this.bg.width !== px;
    // ★★ 寸法が変わっていないなら canvas に一切触らない。
    //   canvas.width への代入は「同じ値でも」中身を消す (HTML 仕様)。
    //   ResizeObserver は寸法が変わらなくても発火するので、ここで抜けないと
    //   「背景 (マス目 + お手本) だけ消えて誰も描き直さない」状態になる。
    //   実際これが「2字目からお手本が消える」の正体だった。
    if (!changed) return;
    this.size = S;
    for (const [c, ctx] of [
      [this.bg, this.bgCtx],
      [this.guide, this.guideCtx],
      [this.ink, this.inkCtx],
    ] as const) {
      c.width = px;
      c.height = px;
      c.style.width = `${S}px`;
      c.style.height = `${S}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    // サイズ再確保で内容が消えるので必ず再描画 (§12.3)
    this.onLayout?.(S);
  }

  /** クライアント座標 → 正規化座標 (0〜1) */
  toNorm(clientX: number, clientY: number): Pt {
    const rect = this.ink.getBoundingClientRect();
    return {
      x: (clientX - rect.left) / rect.width,
      y: (clientY - rect.top) / rect.height,
    };
  }

  dispose(): void {
    this.ro.disconnect();
    window.removeEventListener('orientationchange', this.orientationHandler);
    this.bg.remove();
    this.guide.remove();
    this.ink.remove();
  }
}
