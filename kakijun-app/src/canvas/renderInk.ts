/**
 * ユーザーの筆跡描画 (§5.3)。
 * - 直近3点の二次ベジェ（中点連結）で滑らかにつなぐ
 * - 線幅は S*0.055 基準、筆圧で ±40%
 * - 確定した画は濃い色、書いている画は明るい色
 * 座標は正規化で保持する（リサイズ・回転しても内容を再現できる §14.2）
 */

export type InkPoint = { x: number; y: number; w: number };

const COMMITTED_COLOR = '#37474f';
const CURRENT_COLOR = '#fb8c00';

export class InkRenderer {
  committed: InkPoint[][] = [];
  current: InkPoint[] = [];

  addPoint(x: number, y: number, w: number): void {
    this.current.push({ x, y, w });
  }

  commitCurrent(): void {
    if (this.current.length > 0) this.committed.push(this.current);
    this.current = [];
  }

  clearCurrent(): void {
    this.current = [];
  }

  clearAll(): void {
    this.committed = [];
    this.current = [];
  }

  render(ctx: CanvasRenderingContext2D, size: number): void {
    ctx.clearRect(0, 0, size, size);
    for (const path of this.committed) {
      this.drawPath(ctx, size, path, COMMITTED_COLOR);
    }
    this.drawPath(ctx, size, this.current, CURRENT_COLOR);
  }

  private drawPath(
    ctx: CanvasRenderingContext2D,
    size: number,
    path: InkPoint[],
    color: string,
  ): void {
    if (path.length === 0) return;
    const base = size * 0.055;
    ctx.strokeStyle = color;
    ctx.fillStyle = color;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    if (path.length === 1) {
      ctx.beginPath();
      ctx.arc(path[0].x * size, path[0].y * size, (base * path[0].w) / 2, 0, Math.PI * 2);
      ctx.fill();
      return;
    }
    // 中点連結の二次ベジェ。線幅が筆圧で変わるためセグメントごとに stroke する
    for (let i = 1; i < path.length; i++) {
      const p0 = path[i - 1];
      const p1 = path[i];
      const prev = path[i - 2] ?? p0;
      const m0 = { x: (prev.x + p0.x) / 2, y: (prev.y + p0.y) / 2 };
      const m1 = { x: (p0.x + p1.x) / 2, y: (p0.y + p1.y) / 2 };
      ctx.lineWidth = base * ((p0.w + p1.w) / 2);
      ctx.beginPath();
      ctx.moveTo(m0.x * size, m0.y * size);
      ctx.quadraticCurveTo(p0.x * size, p0.y * size, m1.x * size, m1.y * size);
      ctx.stroke();
    }
    // 終端まで届かせる
    const last = path[path.length - 1];
    const secondLast = path[path.length - 2];
    const mLast = {
      x: (secondLast.x + last.x) / 2,
      y: (secondLast.y + last.y) / 2,
    };
    ctx.lineWidth = base * last.w;
    ctx.beginPath();
    ctx.moveTo(mLast.x * size, mLast.y * size);
    ctx.lineTo(last.x * size, last.y * size);
    ctx.stroke();
  }
}
