/**
 * スタンプ帳 (§9.2)。獲得したスタンプのコレクションを眺める画面。
 */
import { useAppStore } from '../store/appStore';
import { characters } from '../data';
import { computeStamps } from '../store/rewards';
import { BackButton } from './widgets';

export function RewardScreen() {
  const navigate = useAppStore((s) => s.navigate);
  const progress = useAppStore((s) => s.progress);
  const stamps = computeStamps(characters, progress);
  const earned = stamps.filter((s) => s.earned).length;

  return (
    <div
      style={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        padding: 12,
        boxSizing: 'border-box',
      }}
    >
      <header style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <BackButton onClick={() => navigate({ name: 'home' })} />
        <h1 style={{ fontSize: 28, margin: '0 auto', color: 'var(--ink)' }}>
          📖 すたんぷちょう　{earned > 0 && `× ${earned}`}
        </h1>
        <div style={{ width: 64 }} />
      </header>

      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          marginTop: 16,
          display: 'flex',
          flexWrap: 'wrap',
          gap: 16,
          alignContent: 'flex-start',
          justifyContent: 'center',
        }}
      >
        {stamps.map((s) => (
          <div
            key={s.key}
            data-testid={`stamp-${s.key}`}
            style={{
              width: 110,
              height: 110,
              borderRadius: '50%',
              background: s.earned ? '#fff8e1' : '#f2f2f2',
              border: s.earned ? '4px solid var(--accent-warm)' : '4px dashed #ddd',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 56,
              filter: s.earned ? 'none' : 'grayscale(1) opacity(0.35)',
            }}
          >
            {s.earned ? s.emoji : '❔'}
          </div>
        ))}
      </div>
    </div>
  );
}
