import { create } from 'zustand';
import type {
  AttemptSummary,
  CharType,
  GuideLevel,
  Stars,
} from '../engine/types';
import {
  applyAttempt,
  emptyProgress,
  loadAllProgress,
  saveProgress,
  type CharProgress,
} from './progress';
import {
  DEFAULT_SETTINGS,
  loadSettings,
  saveSettings,
  type Settings,
} from './settings';
import { getDB } from './db';
import { audioManager } from '../audio/audioManager';

function applyAudioSettings(s: Settings): void {
  audioManager.voiceEnabled = s.voiceEnabled;
  audioManager.sfxEnabled = s.sfxEnabled;
}

export type Screen =
  | { name: 'home' }
  | { name: 'select'; category: CharType }
  | { name: 'practice'; charId: string }
  | { name: 'reward' }
  | { name: 'parentGate' }
  | { name: 'parentDashboard' }
  | { name: 'timeUp' };

function today(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(
    d.getDate(),
  ).padStart(2, '0')}`;
}

type AppState = {
  screen: Screen;
  ready: boolean;
  settings: Settings;
  progress: Record<string, CharProgress>;
  /** 起動からの練習時間（秒）。練習画面表示中だけ進む (§10.4) */
  sessionSeconds: number;
  /** 端末ローカル日付での今日の合計練習時間（秒） */
  todaySeconds: number;

  navigate: (screen: Screen) => void;
  init: () => Promise<void>;
  recordAttempt: (
    charId: string,
    stars: Stars,
    summary: AttemptSummary,
    guideLevel: GuideLevel,
  ) => void;
  /** 3回連続失敗の自動ダウンなどで、次回の開始レベルを直接更新する */
  setGuideLevel: (charId: string, level: GuideLevel) => void;
  updateSettings: (patch: Partial<Settings>) => void;
  /** 練習画面が1秒ごとに呼ぶ */
  tickPracticeTime: () => void;
  /** 時間制限に達しているか (§10.4)。現在の文字が終わってから発動させる */
  isTimeUp: () => boolean;
  remainingSeconds: () => number | null;
};

export const useAppStore = create<AppState>((set, get) => ({
  screen: { name: 'home' },
  ready: false,
  settings: DEFAULT_SETTINGS,
  progress: {},
  sessionSeconds: 0,
  todaySeconds: 0,

  navigate: (screen) => set({ screen }),

  init: async () => {
    try {
      const [settings, progress, db] = await Promise.all([
        loadSettings(),
        loadAllProgress(),
        getDB(),
      ]);
      const day = await db.get('sessions', today());
      applyAudioSettings(settings);
      set({
        settings,
        progress,
        todaySeconds: day?.seconds ?? 0,
        ready: true,
      });
    } catch {
      // ストレージが使えなくても遊べるようにする（進捗は残らない）
      set({ ready: true });
    }
  },

  recordAttempt: (charId, stars, summary, guideLevel) => {
    const prev = get().progress[charId] ?? emptyProgress(charId);
    const next = applyAttempt(prev, stars, summary, guideLevel, Date.now());
    set({ progress: { ...get().progress, [charId]: next } });
    void saveProgress(next).catch(() => {});
  },

  setGuideLevel: (charId, level) => {
    const prev = get().progress[charId] ?? emptyProgress(charId);
    const next = { ...prev, guideLevel: level };
    set({ progress: { ...get().progress, [charId]: next } });
    void saveProgress(next).catch(() => {});
  },

  updateSettings: (patch) => {
    const next = { ...get().settings, ...patch };
    applyAudioSettings(next);
    set({ settings: next });
    void saveSettings(next).catch(() => {});
  },

  tickPracticeTime: () => {
    const s = get();
    const todaySeconds = s.todaySeconds + 1;
    set({ sessionSeconds: s.sessionSeconds + 1, todaySeconds });
    if (todaySeconds % 10 === 0) {
      void getDB()
        .then((db) => db.put('sessions', { date: today(), seconds: todaySeconds }))
        .catch(() => {});
    }
  },

  isTimeUp: () => {
    const { settings, sessionSeconds, todaySeconds } = get();
    if (settings.sessionLimitMin !== null && sessionSeconds >= settings.sessionLimitMin * 60)
      return true;
    if (settings.dailyLimitMin !== null && todaySeconds >= settings.dailyLimitMin * 60)
      return true;
    return false;
  },

  remainingSeconds: () => {
    const { settings, sessionSeconds, todaySeconds } = get();
    const rems: number[] = [];
    if (settings.sessionLimitMin !== null)
      rems.push(settings.sessionLimitMin * 60 - sessionSeconds);
    if (settings.dailyLimitMin !== null)
      rems.push(settings.dailyLimitMin * 60 - todaySeconds);
    if (rems.length === 0) return null;
    return Math.min(...rems);
  },
}));
