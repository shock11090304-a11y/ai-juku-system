/**
 * 時間制限に達したときの画面 (§10.4)。
 * 「きょうは ここまで！」のイラスト。解除は保護者画面からのみ。
 */
import { useAppStore } from '../store/appStore';

export function TimeUpScreen() {
  const navigate = useAppStore((s) => s.navigate);
  return (
    <div
      style={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 20,
      }}
    >
      <div style={{ fontSize: 110 }}>🌙</div>
      <div style={{ fontSize: 40, color: 'var(--ink)' }}>きょうは ここまで！</div>
      <div style={{ fontSize: 60 }}>😴 ⭐</div>
      <button
        data-testid="btn-gear"
        onClick={() => navigate({ name: 'parentGate' })}
        aria-label="おうちのひとの がめん"
        style={{ background: 'none', fontSize: 20, opacity: 0.45, marginTop: 30 }}
      >
        ⚙️
      </button>
    </div>
  );
}
