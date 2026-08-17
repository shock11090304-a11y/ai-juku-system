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

/** インポートした進捗レコードを安全な形に矯正する */
function sanitizeProgress(p: Record<string, unknown>): CharProgress {
  const base = emptyProgress(p.charId as string);
  const stars = [0, 1, 2, 3].includes(p.bestStars as number)
    ? (p.bestStars as CharProgress['bestStars'])
    : 0;
  const level = [1, 2, 3].includes(p.guideLevel as number)
    ? (p.guideLevel as CharProgress['guideLevel'])
    : 1;
  const counts =
    p.mistakeCounts && typeof p.mistakeCounts === 'object'
      ? (p.mistakeCounts as Record<string, unknown>)
      : {};
  const saneCounts = { ...base.mistakeCounts };
  for (const k of Object.keys(saneCounts) as (keyof typeof saneCounts)[]) {
    if (typeof counts[k] === 'number' && Number.isFinite(counts[k])) {
      saneCounts[k] = counts[k] as number;
    }
  }
  return {
    ...base,
    bestStars: stars,
    guideLevel: level,
    mastered: p.mastered === true,
    attempts: typeof p.attempts === 'number' && Number.isFinite(p.attempts) ? p.attempts : 0,
    lastPlayedAt:
      typeof p.lastPlayedAt === 'number' && Number.isFinite(p.lastPlayedAt)
        ? p.lastPlayedAt
        : 0,
    mistakeCounts: saneCounts,
  };
}

/** インポートした設定を安全な形に矯正する (showTypes: null 等でホームが壊れないように) */
function sanitizeSettings(s: Partial<Settings> | null | undefined): Settings | null {
  if (!s || typeof s !== 'object') return null;
  const limit = (v: unknown, fallback: number | null): number | null =>
    v === null || (typeof v === 'number' && Number.isFinite(v) && v > 0)
      ? (v as number | null)
      : fallback;
  return {
    ...DEFAULT_SETTINGS,
    strictness: ['easy', 'normal', 'strict'].includes(s.strictness as string)
      ? (s.strictness as Settings['strictness'])
      : DEFAULT_SETTINGS.strictness,
    sessionLimitMin: limit(s.sessionLimitMin, DEFAULT_SETTINGS.sessionLimitMin),
    dailyLimitMin: limit(s.dailyLimitMin, DEFAULT_SETTINGS.dailyLimitMin),
    voiceEnabled: s.voiceEnabled !== false,
    sfxEnabled: s.sfxEnabled !== false,
    showTypes: {
      ...DEFAULT_SETTINGS.showTypes,
      ...(s.showTypes && typeof s.showTypes === 'object' ? s.showTypes : {}),
    },
  };
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
  /** 最後に計時した実時刻。PWA が何日も生き続けるため「1回」の区切りに使う */
  lastTickAt: number;
  /** todaySeconds がどの日付のものか（日付跨ぎの検出用） */
  todayKey: string;

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
  weeklySeconds: () => Promise<number>;
  resetTodayTime: () => void;
  exportData: () => Promise<string>;
  importData: (json: string) => Promise<void>;
  clearAllData: () => Promise<void>;
};

export const useAppStore = create<AppState>((set, get) => ({
  screen: { name: 'home' },
  ready: false,
  settings: DEFAULT_SETTINGS,
  progress: {},
  sessionSeconds: 0,
  todaySeconds: 0,
  lastTickAt: 0,
  todayKey: today(),

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
    const now = Date.now();
    const day = today();
    let sessionSeconds = s.sessionSeconds;
    let todaySeconds = s.todaySeconds;
    // ホーム画面 PWA はサスペンドされたまま何日も生きる。
    // 30分以上空いたら新しい「1回のれんしゅう」として数え直す
    if (s.lastTickAt > 0 && now - s.lastTickAt > 30 * 60 * 1000) {
      sessionSeconds = 0;
    }
    // 日付が変わっていたら今日ぶんをリセット（翌朝いきなり時間切れを防ぐ）
    if (s.todayKey !== day) {
      sessionSeconds = 0;
      todaySeconds = 0;
    }
    sessionSeconds += 1;
    todaySeconds += 1;
    set({ sessionSeconds, todaySeconds, lastTickAt: now, todayKey: day });
    if (todaySeconds % 10 === 0) {
      void getDB()
        .then((db) => db.put('sessions', { date: day, seconds: todaySeconds }))
        .catch(() => {});
    }
  },

  /** 今週（直近7日）の練習秒数（保護者ダッシュボード用 §10.2） */
  weeklySeconds: async () => {
    try {
      const db = await getDB();
      const all = await db.getAll('sessions');
      const cutoff = Date.now() - 7 * 24 * 3600 * 1000;
      return all
        .filter((s) => new Date(`${s.date}T00:00:00`).getTime() >= cutoff)
        .reduce((sum, s) => sum + s.seconds, 0);
    } catch {
      return get().todaySeconds;
    }
  },

  /** 保護者操作: 今日のカウントとセッションをリセットして続きを遊べるようにする */
  resetTodayTime: () => {
    set({ sessionSeconds: 0, todaySeconds: 0 });
    void getDB()
      .then((db) => db.put('sessions', { date: today(), seconds: 0 }))
      .catch(() => {});
  },

  /** 進捗+設定+時間の JSON エクスポート (§10.3, §12.6 唯一確実なバックアップ) */
  exportData: async () => {
    const db = await getDB();
    const [progress, sessions] = await Promise.all([
      db.getAll('progress'),
      db.getAll('sessions'),
    ]);
    return JSON.stringify(
      {
        app: 'kakijun',
        version: 1,
        exportedAt: new Date().toISOString(),
        settings: get().settings,
        progress,
        sessions,
      },
      null,
      2,
    );
  },

  importData: async (json: string) => {
    const data = JSON.parse(json) as {
      app?: string;
      version?: number;
      settings?: Partial<Settings> | null;
      progress?: unknown[];
      sessions?: { date?: unknown; seconds?: unknown }[];
    };
    if (data.app !== 'kakijun' || !Array.isArray(data.progress)) {
      throw new Error('かきじゅんのバックアップ JSON ではありません');
    }
    // ★レコードは無検証で保存しない。壊れた1件 (mistakeCounts 欠落など) が
    //   IndexedDB に入ると、以後ダッシュボードが開くたびにクラッシュする
    const progress = data.progress
      .filter(
        (p): p is Record<string, unknown> =>
          !!p && typeof p === 'object' && typeof (p as { charId?: unknown }).charId === 'string',
      )
      .map((p) => sanitizeProgress(p));
    const sessions = (data.sessions ?? []).filter(
      (s): s is { date: string; seconds: number } =>
        !!s && typeof s.date === 'string' && typeof s.seconds === 'number',
    );
    const settings = sanitizeSettings(data.settings);

    const db = await getDB();
    const tx = db.transaction(['progress', 'sessions', 'settings'], 'readwrite');
    // 「復元」なのでマージではなく置き換える (残すとバックアップ後の記録が混ざる)
    await tx.objectStore('progress').clear();
    await tx.objectStore('sessions').clear();
    for (const p of progress) await tx.objectStore('progress').put(p);
    for (const s of sessions) await tx.objectStore('sessions').put(s);
    if (settings) await tx.objectStore('settings').put(settings, 'settings');
    await tx.done;
    await get().init();
  },

  clearAllData: async () => {
    const db = await getDB();
    await Promise.all([
      db.clear('progress'),
      db.clear('sessions'),
    ]);
    set({ progress: {}, sessionSeconds: 0, todaySeconds: 0 });
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
