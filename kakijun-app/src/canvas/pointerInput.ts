/**
 * ★ Pointer Events の正規化・パームリジェクション (§12.2)。
 * - 'pen' を観測している間は 'touch' を無視する。
 *   ★ただし永久ではなく「最後にペンを見てから5分」で解除する。
 *   モジュール変数を無期限に保持すると、ホーム画面 PWA は何日も生き続けるため
 *   一度ペンを使っただけで以後ずっと指で描けなくなる
 * - 手のひら→指の順で触れたとき、動かないポインタ (パーム) を捨てて
 *   後から来たポインタに乗り換える (先着1本勝ちだと描く指が無視される)
 * - setPointerCapture でキャンバス外へのはみ出しに追随する
 * - 筆圧は pen のときだけ採用（指は 0 か 0.5 固定が返るため）
 */
import type { Pt } from '../engine/types';
import type { CanvasSurface } from './CanvasSurface';

// 最後に pen を観測した時刻 (モジュールスコープ・セッション内共有)
let lastPenAt = 0;
const PEN_STICKY_MS = 5 * 60 * 1000;

const penActive = () => Date.now() - lastPenAt < PEN_STICKY_MS;

export type PointerSample = {
  p: Pt;
  /** 0.6〜1.4 の線幅係数（筆圧 ±40% §5.3）。pen 以外は 1.0 */
  widthFactor: number;
};

export type PointerHandlers = {
  onDown: (s: PointerSample) => void;
  onMove: (s: PointerSample) => void;
  onUp: () => void;
  /** 中断。ミス扱いにしないこと (matcher.cancelStroke + ink.clearCurrent) */
  onCancel: () => void;
};

function widthFactor(e: PointerEvent): number {
  if (e.pointerType !== 'pen') return 1;
  const pr = e.pressure > 0 ? e.pressure : 0.5;
  // pressure 0〜1 → 0.6〜1.4
  return 0.6 + Math.min(1, Math.max(0, pr)) * 0.8;
}

export function attachPointerInput(
  surface: CanvasSurface,
  handlers: PointerHandlers,
): () => void {
  const el = surface.ink;
  let activeId: number | null = null;
  let activeType = '';
  let downPos: Pt | null = null;
  let movedDist = 0;

  const begin = (e: PointerEvent) => {
    activeId = e.pointerId;
    activeType = e.pointerType;
    downPos = surface.toNorm(e.clientX, e.clientY);
    movedDist = 0;
    try {
      el.setPointerCapture(e.pointerId);
    } catch {
      // capture できなくても描けるだけ描く
    }
    handlers.onDown({ p: downPos, widthFactor: widthFactor(e) });
  };

  const down = (e: PointerEvent) => {
    if (e.pointerType === 'pen') lastPenAt = Date.now();
    if (penActive() && e.pointerType === 'touch') return; // パーム拒否
    e.preventDefault();
    if (activeId !== null) {
      // すでに1本つかんでいる。原則後着は無視するが、
      // つかんでいるのが「置いただけで動いていない touch」(=パームの疑い) で、
      // 新しいポインタが pen または別の touch なら、そちらに乗り換える
      const grabbedIsStalePalm = activeType === 'touch' && movedDist < 0.015;
      const newcomerWins = e.pointerType === 'pen' || grabbedIsStalePalm;
      if (!newcomerWins) return;
      handlers.onCancel(); // 前のポインタの書きかけは無かったことにする
      begin(e);
      return;
    }
    begin(e);
  };

  const move = (e: PointerEvent) => {
    if (e.pointerId !== activeId) return;
    e.preventDefault();
    // Safari 18.2 未満に getCoalescedEvents は無い。あれば使う (§6.4 注)
    const events: PointerEvent[] =
      typeof e.getCoalescedEvents === 'function' && e.getCoalescedEvents().length > 0
        ? e.getCoalescedEvents()
        : [e];
    for (const ev of events) {
      const p = surface.toNorm(ev.clientX, ev.clientY);
      if (downPos) {
        movedDist += Math.hypot(p.x - downPos.x, p.y - downPos.y);
        downPos = p;
      }
      handlers.onMove({ p, widthFactor: widthFactor(ev) });
    }
  };

  const up = (e: PointerEvent) => {
    if (e.pointerId !== activeId) return;
    activeId = null;
    handlers.onUp();
  };

  const cancel = (e: PointerEvent) => {
    if (e.pointerId !== activeId) return;
    activeId = null;
    handlers.onCancel();
  };

  el.addEventListener('pointerdown', down);
  el.addEventListener('pointermove', move);
  el.addEventListener('pointerup', up);
  el.addEventListener('pointercancel', cancel);
  return () => {
    el.removeEventListener('pointerdown', down);
    el.removeEventListener('pointermove', move);
    el.removeEventListener('pointerup', up);
    el.removeEventListener('pointercancel', cancel);
  };
}
