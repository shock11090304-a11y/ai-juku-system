/**
 * ★ 音声マネージャ (§8)。iOS のアンロック処理を含む。
 * - 事前録音 mp3 (public/audio/...) があればそれを再生、無ければ SpeechSynthesis
 *   (ja-JP, rate 0.85) にフォールバック。あとから音源を差し替えられる (§8.2)
 * - 指示系は割り込み（前を止める）、称賛系はキュー (§8.2)
 * - 称賛・促しは直前に再生したものを除外してランダム選択 (§8.1)
 * - 効果音は WebAudio で合成（柔らかい音色・控えめ §9.2）
 */

import {
  PRAISE,
  RETRY,
  feedbackLine,
  guideText,
  pickDifferent,
  type FeedbackVoiceKind,
} from './voiceLines';

export type SfxKind = 'pop' | 'star' | 'complete' | 'help' | 'stamp' | 'tap';

class AudioManager {
  private ctx: AudioContext | null = null;
  private warmedTTS = false;
  voiceEnabled = true;
  sfxEnabled = true;
  private lastPraise = -1;
  private lastRetry = -1;
  private currentGuideAudio: HTMLAudioElement | null = null;
  /** 存在しないことが分かった音源ファイル（毎回 404 を踏まないため） */
  private missing = new Set<string>();
  /** cancel 直後の speak を1tick遅らせるためのトークン (iOS の無音化バグ回避) */
  private speakSeq = 0;

  constructor() {
    // バックグラウンド復帰で AudioContext が 'interrupted'、
    // SpeechSynthesis が paused のまま固まるのを防ぐ (iPadOS PWA の既知挙動)
    if (typeof document !== 'undefined') {
      document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible') {
          void this.ctx?.resume().catch(() => {});
          if ('speechSynthesis' in window) speechSynthesis.resume();
        }
      });
    }
  }

  /**
   * ユーザー操作を起点に呼ぶ。iOS の自動再生制限を解除する (§8.2 必須)。
   * 何度呼んでもよい（背面化で止まった AudioContext の復帰を兼ねる）
   */
  unlock(): void {
    try {
      if (!this.ctx) {
        this.ctx = new AudioContext();
        const buf = this.ctx.createBuffer(1, 1, 22050);
        const src = this.ctx.createBufferSource();
        src.buffer = buf;
        src.connect(this.ctx.destination);
        src.start(0);
      }
      void this.ctx.resume().catch(() => {});
      // SpeechSynthesis も空発話でウォームアップ（初回のみ）
      if (!this.warmedTTS && 'speechSynthesis' in window) {
        const u = new SpeechSynthesisUtterance('');
        u.volume = 0;
        speechSynthesis.speak(u);
        this.warmedTTS = true;
      }
    } catch {
      // 音が出なくてもアプリは動き続ける
    }
  }

  // ── 音声（ファイル優先 → TTS フォールバック §8.2） ──────────

  private speak(text: string, interrupt: boolean): void {
    if (!('speechSynthesis' in window)) return;
    const seq = ++this.speakSeq;
    const doSpeak = () => {
      if (seq !== this.speakSeq) return; // その後に新しい発話が来ていたら破棄
      // iOS Safari は cancel やバックグラウンド復帰後に paused のまま固まる
      // 既知問題がある。speak 前に必ず resume しておく
      speechSynthesis.resume();
      const u = new SpeechSynthesisUtterance(text);
      u.lang = 'ja-JP';
      u.rate = 0.85;
      speechSynthesis.speak(u);
    };
    if (interrupt) {
      speechSynthesis.cancel();
      // ★cancel と同一 tick の speak は iOS で散発的に無音で落ちるため、
      //   少し置いてから発話する
      setTimeout(doSpeak, 60);
    } else {
      doSpeak();
    }
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
      // 404 では error イベントと play() の reject が両方発火する。
      // 2重に speak しないよう、フォールバックは1回に抑える
      let fellBack = false;
      const fallback = () => {
        if (fellBack) return;
        fellBack = true;
        this.missing.add(file);
        this.speak(text, interrupt);
      };
      audio.onerror = fallback;
      if (interrupt) this.currentGuideAudio = audio;
      audio.play().catch(fallback);
      return;
    }
    this.speak(text, interrupt);
  }

  /**
   * 画の成功時の「じょうず！つぎは ◯かくめ」。
   * 称賛と画数ガイドを1発話にまとめる: 別々にキューへ積むと速書きで
   * TTS が渋滞し、2画ぶん遅れて喋り続けるため。
   * キューが詰まっているときは前を捨てて言い直す
   */
  playStrokeSuccess(nextStrokeNumber: number): void {
    const idx = pickDifferent(PRAISE.length, this.lastPraise);
    this.lastPraise = idx;
    const [, praise] = PRAISE[idx];
    const text = `${praise} ${guideText(nextStrokeNumber, false)}`;
    if (
      'speechSynthesis' in window &&
      (speechSynthesis.pending || speechSynthesis.speaking)
    ) {
      this.playVoice(null, text, true);
    } else {
      this.playVoice(null, text, false);
    }
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
    this.playVoice(
      `guide/stroke_${strokeNumber}`,
      guideText(strokeNumber, isFirst),
      interrupt,
    );
  }

  /** フィードバックの指示音声 (§7.4)。「だめ」「ちがう」は使わない */
  playFeedback(kind: FeedbackVoiceKind, strokeNumber: number): void {
    const line = feedbackLine(kind, strokeNumber);
    this.playVoice(line.file, line.text, true);
  }

  /** ガイドが易しくなったとき (§7.4) */
  playTogether(): void {
    this.playVoice('guide/together', 'いっしょに やってみよう', true);
  }

  /** 称賛。直前と同じものは選ばない (§8.1)。キュー再生 (§8.2) */
  playPraise(): void {
    const idx = pickDifferent(PRAISE.length, this.lastPraise);
    this.lastPraise = idx;
    const [file, text] = PRAISE[idx];
    this.playVoice(`praise/${file}`, text, false);
  }

  /** やり直しの促し。直前と同じものは選ばない */
  playRetryVoice(): void {
    const idx = pickDifferent(RETRY.length, this.lastRetry);
    this.lastRetry = idx;
    const [file, text] = RETRY[idx];
    this.playVoice(`retry/${file}`, text, false);
  }

  // ── 効果音（WebAudio 合成・柔らかい音色 §9.2） ─────────────

  sfx(kind: SfxKind): void {
    if (!this.sfxEnabled || !this.ctx) return;
    // 背面化・画面ロックで 'interrupted'/'suspended' になったままだと全て無音になる。
    // sfx はユーザー操作 (pointerup 等) の中で呼ばれるので resume が効く
    if (this.ctx.state !== 'running') void this.ctx.resume().catch(() => {});
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
