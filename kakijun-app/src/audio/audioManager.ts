/**
 * 音声マネージャ。本実装は Phase 4。
 * ここでは iOS アンロックを含む API 面だけ先に定義しておく (§8.2)。
 */
class AudioManager {
  private ctx: AudioContext | null = null;
  private unlocked = false;

  /** 最初のユーザー操作で呼ぶ。iOS の自動再生制限を解除する */
  unlock(): void {
    if (this.unlocked) return;
    try {
      this.ctx = new AudioContext();
      // 無音バッファを1回鳴らしてアンロック
      const buf = this.ctx.createBuffer(1, 1, 22050);
      const src = this.ctx.createBufferSource();
      src.buffer = buf;
      src.connect(this.ctx.destination);
      src.start(0);
      void this.ctx.resume();
      this.unlocked = true;
    } catch {
      // 音が出なくてもアプリは動き続ける
    }
  }
}

export const audioManager = new AudioManager();
