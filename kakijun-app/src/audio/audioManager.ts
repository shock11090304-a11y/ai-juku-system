/**
 * ★ 音声マネージャ (§8)。iOS のアンロック処理を含む。
 * - 事前録音 mp3 (public/audio/...) があればそれを再生、無ければ SpeechSynthesis
 *   (ja-JP, rate 0.85) にフォールバック。あとから音源を差し替えられる (§8.2)
 * - 指示系は割り込み（前を止める）、称賛系はキュー (§8.2)
 * - 称賛・促しは直前に再生したものを除外してランダム選択 (§8.1)
 * - 効果音は WebAudio で合成（柔らかい音色・控えめ §9.2）
 */

export type SfxKind = 'pop' | 'star' | 'complete' | 'help' | 'stamp' | 'tap';

const PRAISE: [string, string][] = [
  ['praise_01', 'じょうず！'],
  ['praise_02', 'できたね！'],
  ['praise_03', 'すごい！'],
  ['praise_04', 'かっこいい！'],
  ['praise_05', 'きれいに かけたね！'],
  ['praise_06', 'そのちょうし！'],
  ['praise_07', 'ばっちり！'],
  ['praise_08', 'はなまる！'],
  ['praise_09', 'めきめき じょうずに なってるよ！'],
];

const RETRY: [string, string][] = [
  ['retry_01', 'もういちど やってみよう'],
  ['retry_02', 'ゆっくりで いいよ'],
  ['retry_03', 'だいじょうぶ、できるよ'],
  ['retry_04', 'おしい！'],
  ['retry_05', 'すこしずつで いいよ'],
  ['retry_06', 'いっしょに がんばろう'],
];

/** 数の読み（指示音声「◯かくめ」用） */
const KAKU: string[] = ['', 'いっかくめ', 'にかくめ', 'さんかくめ', 'よんかくめ', 'ごかくめ', 'ろっかくめ'];

class AudioManager {
  private ctx: AudioContext | null = null;
  private unlocked = false;
  voiceEnabled = true;
  sfxEnabled = true;
  private lastPraise = -1;
  private lastRetry = -1;
  private currentGuideAudio: HTMLAudioElement | null = null;
  /** 存在しないことが分かった音源ファイル（毎回 404 を踏まないため） */
  private missing = new Set<string>();

  /** 最初のユーザー操作で呼ぶ。iOS の自動再生制限を解除する (§8.2 必須) */
  unlock(): void {
    if (this.unlocked) return;
    try {
      this.ctx = new AudioContext();
      const buf = this.ctx.createBuffer(1, 1, 22050);
      const src = this.ctx.createBufferSource();
      src.buffer = buf;
      src.connect(this.ctx.destination);
      src.start(0);
      void this.ctx.resume();
      // SpeechSynthesis も空発話でウォームアップ
      if ('speechSynthesis' in window) {
        const u = new SpeechSynthesisUtterance('');
        u.volume = 0;
        speechSynthesis.speak(u);
      }
      this.unlocked = true;
    } catch {
      // 音が出なくてもアプリは動き続ける
    }
  }

  // ── 音声（ファイル優先 → TTS フォールバック §8.2） ──────────

  private speak(text: string, interrupt: boolean): void {
    if (!('speechSynthesis' in window)) return;
    if (interrupt) speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = 'ja-JP';
    u.rate = 0.85;
    speechSynthesis.speak(u);
  }

  /**
   * file: public/audio/ 以下の相対パス (拡張子なし)。null なら常に TTS。
   * interrupt: 指示系 true（前の音声を止める）/ 称賛系 false（キュー）
   */
  private playVoice(file: string | null, text: string, interrupt: boolean): void {
    if (!this.voiceEnabled) return;
    if (interrupt && this.currentGuideAudio) {
      this.currentGuideAudio.pause();
      this.currentGuideAudio = null;
    }
    if (file && !this.missing.has(file)) {
      const url = `${import.meta.env.BASE_URL}audio/${file}.mp3`;
      const audio = new Audio(url);
      audio.onerror = () => {
        this.missing.add(file);
        this.speak(text, interrupt);
      };
      if (interrupt) this.currentGuideAudio = audio;
      audio.play().catch(() => {
        this.missing.add(file);
        this.speak(text, interrupt);
      });
      return;
    }
    this.speak(text, interrupt);
  }

  /** 文字の読み上げ（🔊 タップ・文字表示時） */
  playReading(charId: string, reading: string): void {
    this.playVoice(`char/${charId}`, reading, true);
  }

  /** 絵カードの語 */
  playWord(audioFile: string | undefined, word: string): void {
    const file = audioFile ? audioFile.replace(/\.mp3$/, '') : null;
    this.playVoice(file, word, true);
  }

  /**
   * 「いっかくめ」「つぎは にかくめ」などの指示。
   * 画の成功直後は称賛をかき消さないよう interrupt=false で呼ぶ
   */
  playStrokeGuide(strokeNumber: number, isFirst: boolean, interrupt = true): void {
    const kaku = KAKU[strokeNumber] ?? `${strokeNumber}かくめ`;
    const text = isFirst ? kaku : `つぎは ${kaku}`;
    this.playVoice(`guide/stroke_${strokeNumber}`, text, interrupt);
  }

  /** フィードバックの指示音声 (§7.4)。「だめ」「ちがう」は使わない */
  playFeedback(kind: 'start' | 'order' | 'offpath' | 'reverse' | 'short', strokeNumber: number): void {
    switch (kind) {
      case 'start':
        return this.playVoice('guide/start_here', 'ここから はじめてね', true);
      case 'order': {
        const kaku = KAKU[strokeNumber] ?? `${strokeNumber}かくめ`;
        return this.playVoice(`guide/next_is_${strokeNumber}`, `つぎは ${kaku}だよ`, true);
      }
      case 'offpath':
        return this.playVoice('guide/on_line', 'せんの うえを なぞろうね', true);
      case 'reverse':
        return this.playVoice('guide/this_way', 'こっちむきだよ', true);
      case 'short':
        return this.playVoice('guide/to_end', 'さいごまで なぞろうね', true);
    }
  }

  /** ガイドが易しくなったとき (§7.4) */
  playTogether(): void {
    this.playVoice('guide/together', 'いっしょに やってみよう', true);
  }

  /** 称賛。直前と同じものは選ばない (§8.1)。キュー再生 (§8.2) */
  playPraise(): void {
    const idx = this.pickIndex(PRAISE.length, this.lastPraise);
    this.lastPraise = idx;
    const [file, text] = PRAISE[idx];
    this.playVoice(`praise/${file}`, text, false);
  }

  /** やり直しの促し。直前と同じものは選ばない */
  playRetryVoice(): void {
    const idx = this.pickIndex(RETRY.length, this.lastRetry);
    this.lastRetry = idx;
    const [file, text] = RETRY[idx];
    this.playVoice(`retry/${file}`, text, false);
  }

  private pickIndex(n: number, exclude: number): number {
    let idx = Math.floor(Math.random() * (n - 1));
    if (idx >= exclude && exclude >= 0) idx++;
    return idx % n;
  }

  // ── 効果音（WebAudio 合成・柔らかい音色 §9.2） ─────────────

  sfx(kind: SfxKind): void {
    if (!this.sfxEnabled || !this.ctx) return;
    const t = this.ctx.currentTime;
    switch (kind) {
      case 'pop':
        this.tone(660, t, 0.09, 0.12, 'sine');
        break;
      case 'star':
        this.tone(784, t, 0.08, 0.1, 'sine');
        this.tone(1175, t + 0.08, 0.12, 0.1, 'sine');
        break;
      case 'complete':
        this.tone(523, t, 0.12, 0.12, 'sine');
        this.tone(659, t + 0.12, 0.12, 0.12, 'sine');
        this.tone(784, t + 0.24, 0.2, 0.12, 'sine');
        break;
      case 'help':
        this.tone(440, t, 0.15, 0.08, 'sine');
        this.tone(523, t + 0.15, 0.2, 0.08, 'sine');
        break;
      case 'stamp':
        this.tone(392, t, 0.1, 0.14, 'triangle');
        this.tone(523, t + 0.1, 0.16, 0.12, 'triangle');
        break;
      case 'tap':
        this.tone(880, t, 0.05, 0.06, 'sine');
        break;
    }
  }

  private tone(
    freq: number,
    at: number,
    dur: number,
    vol: number,
    type: OscillatorType,
  ): void {
    if (!this.ctx) return;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.type = type;
    osc.frequency.value = freq;
    gain.gain.setValueAtTime(0, at);
    gain.gain.linearRampToValueAtTime(vol, at + 0.015);
    gain.gain.exponentialRampToValueAtTime(0.001, at + dur);
    osc.connect(gain).connect(this.ctx.destination);
    osc.start(at);
    osc.stop(at + dur + 0.05);
  }
}

export const audioManager = new AudioManager();
