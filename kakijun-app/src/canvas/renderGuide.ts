/**
 * お手本・点線・番号・矢印・お手本アニメ・フィードバック演出の描画 (§5.4, §7.4)。
 * 背景層 = 文字が変わったときだけ描き直す / ガイド層 = 毎フレーム。
 * 赤色は「間違い」の意味で使わない (§11-6)。強調はオレンジ・黄色。
 */
import type { GuideLevel, Pt, ResampledStroke } from '../engine/types';

const GUIDE_DOT = '#b0bec5'; // Lv1 点線
const GUIDE_SOLID = '#cfd8dc'; // Lv2 うすいお手本
const ACCENT = '#ffb74d';
const ACCENT_STRONG = '#fb8c00';
const NUM_COLOR = '#4fc3f7';

type Effect =
  | { kind: 'pulse'; t0: number; dur: number }
  | { kind: 'glow'; t0: number; dur: number }
  | { kind: 'arrowfx'; t0: number; dur: number }
  | { kind: 'zoom'; t0: number; dur: number }
  | { kind: 'burst'; t0: number; dur: number; at: Pt };

function tangentAt(s: ResampledStroke, i: number): Pt {
  const a = s.pts[Math.max(0, i - 1)];
  const b = s.pts[Math.min(63, i + 1)];
  const l = Math.hypot(b.x - a.x, b.y - a.y) || 1;
  return { x: (b.x - a.x) / l, y: (b.y - a.y) / l };
}

export class GuideRenderer {
  strokes: ResampledStroke[] = [];
  level: GuideLevel = 1;
  strokeIdx = 0;
  private effects: Effect[] = [];
  private demo: { t0: number } | null = null;
  /** アニメが必要なフレームがあるか（rAF の省エネ判定に使える） */
  get busy(): boolean {
    return this.effects.length > 0 || this.demo !== null;
  }

  setCharacter(strokes: ResampledStroke[], level: GuideLevel): void {
    this.strokes = strokes;
    this.level = level;
    this.strokeIdx = 0;
    this.effects = [];
    this.demo = null;
  }

  playDemo(): void {
    if (this.level === 1) this.demo = { t0: performance.now() };
  }
  pulseStart(): void {
    this.effects.push({ kind: 'pulse', t0: performance.now(), dur: 1300 });
  }
  glowPath(): void {
    this.effects.push({ kind: 'glow', t0: performance.now(), dur: 1300 });
  }
  arrowHint(): void {
    this.effects.push({ kind: 'arrowfx', t0: performance.now(), dur: 1400 });
  }
  zoomNumber(): void {
    this.effects.push({ kind: 'zoom', t0: performance.now(), dur: 1000 });
  }
  burst(at: Pt): void {
    this.effects.push({ kind: 'burst', t0: performance.now(), dur: 700, at });
  }

  /** 背景層: マス目 + 文字全体のお手本 (§5.1) */
  renderBackground(ctx: CanvasRenderingContext2D, size: number): void {
    ctx.clearRect(0, 0, size, size);
    // 十字の点線マス
    ctx.strokeStyle = '#e0e0e0';
    ctx.lineWidth = 2;
    ctx.setLineDash([8, 10]);
    ctx.beginPath();
    ctx.moveTo(size / 2, 0);
    ctx.lineTo(size / 2, size);
    ctx.moveTo(0, size / 2);
    ctx.lineTo(size, size / 2);
    ctx.stroke();
    ctx.setLineDash([]);
    if (this.level === 2) {
      // うすいグレーの文字
      for (const s of this.strokes) this.path(ctx, size, s, 0, 63);
      ctx.strokeStyle = GUIDE_SOLID;
      ctx.lineWidth = size * 0.11;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      for (const s of this.strokes) {
        this.path(ctx, size, s, 0, 63);
        ctx.stroke();
      }
    }
  }

  /** ガイド層: 毎フレーム (§5.1) */
  renderFrame(ctx: CanvasRenderingContext2D, size: number, now: number): void {
    ctx.clearRect(0, 0, size, size);
    this.effects = this.effects.filter((e) => now - e.t0 < e.dur);
    const cur = this.strokes[this.strokeIdx];

    if (this.level === 1) {
      // まだ書いていない画の太い点線
      for (let i = this.strokeIdx; i < this.strokes.length; i++) {
        this.dottedStroke(ctx, size, this.strokes[i], i === this.strokeIdx);
      }
    }
    if (this.level <= 2) {
      // 画数の数字（確定済みは消す）
      for (let i = this.strokeIdx; i < this.strokes.length; i++) {
        this.strokeNumber(ctx, size, this.strokes[i], i === this.strokeIdx, now);
      }
      // 始点の光る丸（パルス）
      if (cur) this.startDot(ctx, size, cur, now);
      // 方向の矢印 (Lv1)
      if (this.level === 1 && cur) this.arrow(ctx, size, cur, 0.2, ACCENT_STRONG);
    }

    // お手本アニメ (Lv1)
    if (this.demo && cur) {
      const t = (now - this.demo.t0) / 1300;
      if (t >= 1.15) {
        this.demo = null;
      } else {
        const k = Math.max(1, Math.floor(Math.min(1, t) * 63));
        ctx.strokeStyle = ACCENT;
        ctx.globalAlpha = 0.9;
        ctx.lineWidth = size * 0.09;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        this.path(ctx, size, cur, 0, k);
        ctx.stroke();
        ctx.globalAlpha = 1;
        const tip = cur.pts[k];
        ctx.fillStyle = ACCENT_STRONG;
        ctx.beginPath();
        ctx.arc(tip.x * size, tip.y * size, size * 0.035, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    // フィードバック演出
    for (const e of this.effects) {
      const t = (now - e.t0) / e.dur;
      if (e.kind === 'pulse' && cur) {
        // 始点の丸を3回大きく点滅 (§7.4)
        const phase = (t * 3) % 1;
        const r = size * (0.045 + 0.05 * phase);
        ctx.strokeStyle = ACCENT_STRONG;
        ctx.globalAlpha = 1 - phase;
        ctx.lineWidth = size * 0.015;
        ctx.beginPath();
        ctx.arc(cur.pts[0].x * size, cur.pts[0].y * size, r, 0, Math.PI * 2);
        ctx.stroke();
        ctx.globalAlpha = 1;
      } else if (e.kind === 'glow' && cur) {
        // 現在の画の点線が明るく光る (§7.4)
        ctx.globalAlpha = 0.5 + 0.5 * Math.sin(t * Math.PI * 4);
        ctx.strokeStyle = '#ffd54f';
        ctx.lineWidth = size * 0.12;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        this.path(ctx, size, cur, 0, 63);
        ctx.stroke();
        ctx.globalAlpha = 1;
      } else if (e.kind === 'arrowfx' && cur) {
        // 矢印が進行方向へ流れる (§7.4 逆向き)
        for (let a = 0; a < 3; a++) {
          const pos = ((t * 1.5 + a / 3) % 1) * 0.9;
          this.arrow(ctx, size, cur, pos, ACCENT_STRONG);
        }
      } else if (e.kind === 'zoom' && cur) {
        // 正しい画の番号を拡大表示 (§7.4 書き順違い)
        const scale = 2.6 - 1.6 * Math.min(1, t * 1.4);
        this.strokeNumber(ctx, size, cur, true, now, scale);
      } else if (e.kind === 'burst') {
        // 小さな星が飛ぶ (§7.4 画の成功)
        for (let i = 0; i < 7; i++) {
          const ang = (i / 7) * Math.PI * 2 + 0.5;
          const dist = size * 0.12 * t;
          const x = e.at.x * size + Math.cos(ang) * dist;
          const y = e.at.y * size + Math.sin(ang) * dist + size * 0.04 * t * t;
          ctx.globalAlpha = 1 - t;
          this.star(ctx, x, y, size * 0.018);
          ctx.globalAlpha = 1;
        }
      }
    }
  }

  private path(
    ctx: CanvasRenderingContext2D,
    size: number,
    s: ResampledStroke,
    from: number,
    to: number,
  ): void {
    ctx.beginPath();
    ctx.moveTo(s.pts[from].x * size, s.pts[from].y * size);
    for (let i = from + 1; i <= to; i++) {
      ctx.lineTo(s.pts[i].x * size, s.pts[i].y * size);
    }
  }

  private dottedStroke(
    ctx: CanvasRenderingContext2D,
    size: number,
    s: ResampledStroke,
    isCurrent: boolean,
  ): void {
    const lw = size * 0.085;
    ctx.strokeStyle = isCurrent ? '#90caf9' : GUIDE_DOT;
    ctx.lineWidth = lw;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    // 点線が「線」として読めるよう、点の間隔は点径の半分強にする
    ctx.setLineDash([0.01, lw * 0.62]);
    this.path(ctx, size, s, 0, 63);
    ctx.stroke();
    ctx.setLineDash([]);
  }

  private strokeNumber(
    ctx: CanvasRenderingContext2D,
    size: number,
    s: ResampledStroke,
    isCurrent: boolean,
    _now: number,
    scale = 1,
  ): void {
    const p = s.pts[0];
    const t = tangentAt(s, 0);
    // 始点から進行方向と逆側に少しずらして置く
    const ox = -t.x * size * 0.07 - t.y * size * 0.03;
    const oy = -t.y * size * 0.07 + t.x * size * 0.03;
    const x = Math.min(size * 0.95, Math.max(size * 0.05, p.x * size + ox));
    const y = Math.min(size * 0.95, Math.max(size * 0.05, p.y * size + oy));
    const r = size * (isCurrent ? 0.045 : 0.032) * scale;
    ctx.fillStyle = '#fff';
    ctx.strokeStyle = isCurrent ? ACCENT_STRONG : NUM_COLOR;
    ctx.lineWidth = size * 0.008;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = isCurrent ? ACCENT_STRONG : NUM_COLOR;
    ctx.font = `bold ${r * 1.3}px sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(String(s.index), x, y + r * 0.05);
  }

  private startDot(
    ctx: CanvasRenderingContext2D,
    size: number,
    s: ResampledStroke,
    now: number,
  ): void {
    if (this.level === 3) return; // Lv3 では出さない (§5.4)
    const p = s.pts[0];
    const pulse = 0.5 + 0.5 * Math.sin(now / 280);
    ctx.fillStyle = ACCENT_STRONG;
    ctx.globalAlpha = 0.25 + 0.2 * pulse;
    ctx.beginPath();
    ctx.arc(p.x * size, p.y * size, size * (0.05 + 0.012 * pulse), 0, Math.PI * 2);
    ctx.fill();
    ctx.globalAlpha = 1;
    ctx.beginPath();
    ctx.arc(p.x * size, p.y * size, size * 0.028, 0, Math.PI * 2);
    ctx.fill();
  }

  private arrow(
    ctx: CanvasRenderingContext2D,
    size: number,
    s: ResampledStroke,
    posRatio: number,
    color: string,
  ): void {
    const i = Math.min(62, Math.max(1, Math.floor(posRatio * 63)));
    const p = s.pts[i];
    const t = tangentAt(s, i);
    const a = Math.atan2(t.y, t.x);
    ctx.save();
    ctx.translate(p.x * size, p.y * size);
    ctx.rotate(a);
    ctx.strokeStyle = color;
    ctx.lineWidth = size * 0.014;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    const r = size * 0.028;
    ctx.beginPath();
    ctx.moveTo(-r, -r);
    ctx.lineTo(r * 0.9, 0);
    ctx.lineTo(-r, r);
    ctx.stroke();
    ctx.restore();
  }

  private star(ctx: CanvasRenderingContext2D, x: number, y: number, r: number): void {
    ctx.fillStyle = '#ffca28';
    ctx.beginPath();
    for (let i = 0; i < 10; i++) {
      const ang = (i / 10) * Math.PI * 2 - Math.PI / 2;
      const rr = i % 2 === 0 ? r : r * 0.45;
      const px = x + Math.cos(ang) * rr;
      const py = y + Math.sin(ang) * rr;
      i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
    }
    ctx.closePath();
    ctx.fill();
  }
}
