import { create } from 'zustand';
import type { CharType } from '../engine/types';

export type Screen =
  | { name: 'home' }
  | { name: 'select'; category: CharType }
  | { name: 'practice'; charId: string }
  | { name: 'reward' }
  | { name: 'parentGate' }
  | { name: 'parentDashboard' }
  | { name: 'timeUp' };

type AppState = {
  screen: Screen;
  navigate: (screen: Screen) => void;
  init: () => Promise<void>;
};

export const useAppStore = create<AppState>((set) => ({
  screen: { name: 'home' },
  navigate: (screen) => set({ screen }),
  init: async () => {
    // 進捗・設定の読み込みは Phase 5/6 で実装
  },
}));
