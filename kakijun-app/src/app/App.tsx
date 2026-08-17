import { useEffect } from 'react';
import { useAppStore } from '../store/appStore';
import { HomeScreen } from './HomeScreen';
import { CharSelectScreen } from './CharSelectScreen';
import { PracticeScreen } from './PracticeScreen';
import { RewardScreen } from './RewardScreen';
import { ParentGate } from './ParentGate';
import { ParentDashboard } from './ParentDashboard';
import { TimeUpScreen } from './TimeUpScreen';
import { audioManager } from '../audio/audioManager';

/** 縦向きのとき「iPad を よこに してね」の案内 (§2.3) */
function RotateHint() {
  return (
    <div className="rotate-hint">
      <svg width="160" height="160" viewBox="0 0 160 160" aria-hidden>
        <rect x="30" y="55" width="100" height="66" rx="10" fill="none" stroke="#90a4ae" strokeWidth="6" />
        <circle cx="120" cy="88" r="5" fill="#90a4ae" />
        <path d="M 80 30 A 45 45 0 0 1 125 45" fill="none" stroke="#ffb74d" strokeWidth="8" strokeLinecap="round" />
        <path d="M 118 30 L 128 47 L 108 50 Z" fill="#ffb74d" />
      </svg>
      <div style={{ fontSize: 28, color: '#90a4ae' }}>よこに してね</div>
    </div>
  );
}

export function App() {
  const screen = useAppStore((s) => s.screen);
  const init = useAppStore((s) => s.init);

  useEffect(() => {
    void init();
  }, [init]);

  // iOS の自動再生制限: ユーザー操作で音をアンロックする (§8.2)。
  // 一発勝負にせず張りっぱなしにする: unlock は冪等で、
  // 背面化で止まった AudioContext の復帰 (resume) も兼ねる。
  // touch では pointerup/click 側が user activation として確実
  useEffect(() => {
    const unlock = () => audioManager.unlock();
    window.addEventListener('pointerdown', unlock);
    window.addEventListener('pointerup', unlock);
    window.addEventListener('click', unlock);
    return () => {
      window.removeEventListener('pointerdown', unlock);
      window.removeEventListener('pointerup', unlock);
      window.removeEventListener('click', unlock);
    };
  }, []);

  return (
    <>
      <RotateHint />
      {screen.name === 'home' && <HomeScreen />}
      {screen.name === 'select' && <CharSelectScreen />}
      {screen.name === 'practice' && <PracticeScreen />}
      {screen.name === 'reward' && <RewardScreen />}
      {screen.name === 'parentGate' && <ParentGate />}
      {screen.name === 'parentDashboard' && <ParentDashboard />}
      {screen.name === 'timeUp' && <TimeUpScreen />}
    </>
  );
}
