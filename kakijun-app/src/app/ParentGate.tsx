/**
 * 保護者ゲート (§10.1)。幼児が突破できない認証。
 * 二桁になる掛け算を毎回ランダム生成。数字キーパッド。3回間違えたらホームへ。
 * PIN 方式にはしない。
 */
import { useMemo, useState } from 'react';
import { useAppStore } from '../store/appStore';

function newQuestion(): { a: number; b: number } {
  // 積が必ず二桁になる組み合わせ (3×4=12 以上)
  for (;;) {
    const a = 3 + Math.floor(Math.random() * 7); // 3..9
    const b = 3 + Math.floor(Math.random() * 7);
    if (a * b >= 10) return { a, b };
  }
}

export function ParentGate() {
  const navigate = useAppStore((s) => s.navigate);
  const [q, setQ] = useState(newQuestion);
  const [input, setInput] = useState('');
  const [fails, setFails] = useState(0);
  const answer = useMemo(() => String(q.a * q.b), [q]);

  function press(d: string) {
    if (input.length >= 3) return;
    setInput(input + d);
  }

  function submit() {
    if (input === answer) {
      navigate({ name: 'parentDashboard' });
      return;
    }
    const f = fails + 1;
    if (f >= 3) {
      navigate({ name: 'home' });
      return;
    }
    setFails(f);
    setQ(newQuestion());
    setInput('');
  }

  return (
    <div
      style={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 14,
      }}
    >
      <div style={{ fontSize: 20, color: '#78909c' }}>おうちの人へ</div>
      <div style={{ fontSize: 30 }}>
        <b>
          {q.a} × {q.b}
        </b>{' '}
        の答えを入力してください
      </div>
      <div
        data-testid="gate-input"
        style={{
          fontSize: 40,
          letterSpacing: 8,
          minHeight: 56,
          minWidth: 140,
          textAlign: 'center',
          borderBottom: '3px solid var(--accent-warm)',
        }}
      >
        {input || '　'}
      </div>
      {fails > 0 && (
        <div style={{ color: '#e65100', fontSize: 16 }}>
          もう一度どうぞ（あと {3 - fails} 回）
        </div>
      )}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 76px)',
          gap: 10,
        }}
      >
        {['1', '2', '3', '4', '5', '6', '7', '8', '9', '←', '0', 'OK'].map(
          (k) => (
            <button
              key={k}
              data-testid={`key-${k}`}
              className="tap-target"
              onClick={() => {
                if (k === '←') setInput(input.slice(0, -1));
                else if (k === 'OK') submit();
                else press(k);
              }}
              style={{
                height: 64,
                fontSize: 26,
                borderRadius: 14,
                background: k === 'OK' ? 'var(--accent-warm)' : 'var(--card-bg)',
                boxShadow: 'var(--shadow)',
              }}
            >
              {k}
            </button>
          ),
        )}
      </div>
      <button
        className="tap-target"
        onClick={() => navigate({ name: 'home' })}
        style={{ marginTop: 8, fontSize: 18, background: 'none', color: '#90a4ae' }}
      >
        もどる
      </button>
    </div>
  );
}
