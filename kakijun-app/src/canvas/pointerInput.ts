/**
 * ★ Pointer Events の正規化・パームリジェクション (§12.2)。
 * - 'pen' を一度でも観測したら、以降 'touch' を完全に無視する
 *   （penDetected はセッション中保持。文字の切り替えではリセットしない）
 * - setPointerCapture でキャンバス外へのはみ出しに追随する
 * - 筆圧は pen のときだけ採用（指は 0 か 0.5 固定が返るため）
 */
import type { Pt } from '../engine/types';
import type { CanvasSurface } from './CanvasSurface';

// セッション中保持（モジュールスコープ）
let penDetected = false;

export type PointerSample = {
  p: Pt;
  /** 0.6〜1.4 の線幅係数（筆圧 ±40% §5.3）。pen 以外は 1.0 */
  widthFactor: number;
};

export type PointerHandlers = {
  onDown: (s: PointerSample) => void;
  onMove: (s: PointerSample) => void;
  onUp: () => void;
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

  const down = (e: PointerEvent) => {
    if (e.pointerType === 'pen') penDetected = true;
    if (penDetected && e.pointerType === 'touch') return; // パーム拒否
    if (activeId !== null) return; // 2本目以降は無視
    activeId = e.pointerId;
    el.setPointerCapture(e.pointerId);
    e.preventDefault();
    handlers.onDown({ p: surface.toNorm(e.clientX, e.clientY), widthFactor: widthFactor(e) });
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
      handlers.onMove({
        p: surface.toNorm(ev.clientX, ev.clientY),
        widthFactor: widthFactor(ev),
      });
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
