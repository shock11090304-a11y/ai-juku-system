/**
 * お手本・点線・番号・矢印・お手本アニメ・フィードバック演出の描画 (§5.4, §7.4)。
 * 背景層 = 文字が変わったときだけ描き直す / ガイド層 = 毎フレーム。
 * 赤色は「間違い」の意味で使わない (§11-6)。強調はオレンジ・黄色。
 */
import type { GuideLevel, Pt, ResampledStroke } from '../engine/types';
import { drawSampleGlyph } from './sampleGlyph';

const GUIDE_SOLID = '#cfd8dc'; // お手本の字 (全レベル共通・消さない)
const ACCENT = '#ffb74d';
const ACCENT_STRONG = '#fb8c00';
const NUM_COLOR = '#4fc3f7';

type Effect =
  | { kind: 'pulse'; t0: number; dur: number }
  | { kind: 'glow'; t0: number; dur: number }
  | { kind: 'arrowfx'; t0: number; dur: number }
  | { kind: 'zoom'; t0: number; dur: number }
  | { kind: 'burst'; t0: number; dur: number; at: Pt };

/**
 * 進行方向。★隣り合う2点で測らないこと。
 * 判定用の線データは手本フォントの墨に合わせ込んであり、1〜2点ぶんの
 * 細かい凹凸が乗っている。2点だけで測ると、まっすぐ右へ進む画なのに
 * 「上向き」と出て、矢印も番号も見当違いの向きになる
 * (か の1画目で -72度。画全体は +60度。2026-08-17 塾長指摘)。
 * 弧長で 1割ぶん (±6点) 離して測り、細かい揺れを均す。
 */
const DIR_SPAN = 6;
function tangentAt(s: ResampledStroke, i: number, span = DIR_SPAN): Pt {
  const a = s.pts[Math.max(0, i - span)];
  const b = s.pts[Math.min(63, i + span)];
  const l = Math.hypot(b.x - a.x, b.y - a.y) || 1;
  return { x: (b.x - a.x) / l, y: (b.y - a.y) / l };
}

/**
 * 書き出しの向き = 始点から弧長 2割ぶん先の点へ向かう向き。
 * ★局所の接線を使わないこと。線データは書き出し付近でお手本から外れている字が
 *   あり (か の1画目は局所 -52度・お手本の横画は -9度)、局所接線で矢印を描くと
 *   「お手本と違う向き」を指す。始点から離れた点へ向かう向きなら、
 *   多少の凹凸があっても「点から、こっちへ」を正しく示せる。
 */
const START_DIR_SPAN = 12;
function startDirection(s: ResampledStroke): Pt {
  const b = s.pts[Math.min(63, START_DIR_SPAN)];
  const l = Math.hypot(b.x - s.pts[0].x, b.y - s.pts[0].y) || 1;
  return { x: (b.x - s.pts[0].x) / l, y: (b.y - s.pts[0].y) / l };
}

export class GuideRenderer {
  strokes: ResampledStroke[] = [];
  /** お手本として描く字。線データではなくフォントで描く (字形が崩れないように) */
  char = '';
  level: GuideLevel = 1;
  strokeIdx = 0;
  private effects: Effect[] = [];
  private demo: { t0: number } | null = null;
  /** アニメが必要なフレームがあるか（rAF の省エネ判定に使える） */
  get busy(): boolean {
    return this.effects.length > 0 || this.demo !== null;
  }

  setCharacter(strokes: ResampledStroke[], level: GuideLevel, char = ''): void {
    this.strokes = strokes;
    this.char = char;
    this.level = level;
    this.strokeIdx = 0;
    this.effects = [];
    this.demo = null;
  }

  playDemo(): void {
    // 経路をなぞるアニメも同じ理由で出さない
    this.demo = null;
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
    // お手本の字はフォントで描く。線データ (判定用) の形に依存させない。
    // ★ お手本はどのレベルでも消さない (塾長方針: 何度でも練習できるように)。
    //   濃さも変えない。薄くすると「消えた」と同じで練習にならない。
    if (this.char) {
      // 描き方は src/canvas/sampleGlyph.ts が正典 (字形ツールと共有)
      drawSampleGlyph(ctx, this.char, size, GUIDE_SOLID);
    } else {
      // ★ 運筆 (なみなみ・ぐるぐる・かいだん等) は「字」ではないので手本フォントが無い。
      //   文字コード (〽 ◎ 🪜 ⛰) を借りて描くと、絵文字や別物の記号が出てしまい、
      //   しかも判定する線とは似ても似つかない形になる。
      //   運筆に限りお手本を線データそのものから描く。この場合お手本と判定は
      //   同一データなので「お手本と違う線を見せる」問題 (PR #39) は起きない。
      this.sampleFromStrokes(ctx, size);
    }
  }

  /** 運筆用: 判定に使う線データ自体をお手本として描く */
  private sampleFromStrokes(ctx: CanvasRenderingContext2D, size: number): void {
    if (this.strokes.length === 0) return;
    ctx.save();
    ctx.strokeStyle = GUIDE_SOLID;
    ctx.lineWidth = size * 0.075; // 手本フォントの縦画とほぼ同じ太さ
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    for (const s of this.strokes) {
      this.path(ctx, size, s, 0, 63);
      ctx.stroke();
    }
    ctx.restore();
  }

  /** ガイド層: 毎フレーム (§5.1) */
  renderFrame(ctx: CanvasRenderingContext2D, size: number, now: number): void {
    ctx.clearRect(0, 0, size, size);
    this.effects = this.effects.filter((e) => now - e.t0 < e.dur);
    const cur = this.strokes[this.strokeIdx];

    // ★ 画の経路をなぞって見せる表示はしない。
    //   お手本はフォント、判定は線データで、両者の経路が一致しないため、
    //   経路を描くと「お手本と違う線」を子どもに見せることになる (塾長指摘)。
    //   書き順は「番号 + 書き出しの点」だけで示す (なぞり書きプリントと同じ方式)。
    if (this.level <= 2) {
      // 画数の数字（確定済みは消す）
      for (let i = this.strokeIdx; i < this.strokes.length; i++) {
        this.strokeNumber(ctx, size, this.strokes[i], i === this.strokeIdx, now);
      }
      // 始点の光る丸（パルス）
      if (cur) this.startDot(ctx, size, cur, now);
      // 方向の矢印 (Lv1)。★書き出しの点のすぐ先に、書き出しの向きで置く。
      //   「点から、こっちへ」を示すもの。画の途中の接線で描くと、
      //   折れ角に当たったときお手本と無関係な向きを指す
      if (this.level === 1 && cur) {
        this.arrow(ctx, size, cur.pts[Math.min(63, 10)], startDirection(cur), ACCENT_STRONG);
      }
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
          const i = Math.min(62, Math.max(1, Math.floor(pos * 63)));
          this.arrow(ctx, size, cur.pts[i], tangentAt(cur, i), ACCENT_STRONG);
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


  private strokeNumber(
    ctx: CanvasRenderingContext2D,
    size: number,
    s: ResampledStroke,
    isCurrent: boolean,
    _now: number,
    scale = 1,
  ): void {
    const p = s.pts[0];
    const t = startDirection(s);
    // 始点から進行方向と逆側に少しずらして置く。
    // ★ずらし幅は「番号の丸が書き出しの点に触れる」程度に留める。
    //   離すと、どの画の番号なのか分からなくなる (塾長指摘)
    const ox = -t.x * size * 0.055 - t.y * size * 0.022;
    const oy = -t.y * size * 0.055 + t.x * size * 0.022;
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
    p: Pt,
    t: Pt,
    color: string,
  ): void {
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
