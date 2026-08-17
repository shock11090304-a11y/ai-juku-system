/**
 * 文字えらび画面 (§7.2)。
 * あ行を1行目とする横並びグリッド。達成状態を星で表示。ロックはしない。
 * 濁音・半濁音・小さい字は別タブ。
 */
import { useState } from 'react';
import { useAppStore } from '../store/appStore';
import { groupsOf, listByType } from '../data';
import { audioManager } from '../audio/audioManager';
import type { CharType } from '../engine/types';
import { BackButton } from './widgets';

const SEION_TABS: Record<string, (group: string) => boolean> = {
  せいおん: (g) => g.endsWith('-gyo'),
  だくおん: (g) => g === 'dakuon' || g === 'handakuon',
  ちいさいじ: (g) => g === 'youon',
};

export function CharSelectScreen() {
  const screen = useAppStore((s) => s.screen);
  const navigate = useAppStore((s) => s.navigate);
  const progress = useAppStore((s) => s.progress);
  const category: CharType = screen.name === 'select' ? screen.category : 'hiragana';
  const isKana = category === 'hiragana' || category === 'katakana';
  const [tab, setTab] = useState('せいおん');

  const chars = listByType(category);
  const groups = groupsOf(category).filter((g) =>
    isKana ? SEION_TABS[tab]?.(g) : true,
  );
  const tabHasContent = (t: string) =>
    groupsOf(category).some((g) => SEION_TABS[t](g));

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
        {isKana && (
          <div style={{ display: 'flex', gap: 8, margin: '0 auto' }}>
            {Object.keys(SEION_TABS)
              .filter(tabHasContent)
              .map((t) => (
                <button
                  key={t}
                  className="tap-target"
                  onClick={() => setTab(t)}
                  style={{
                    fontSize: 20,
                    padding: '8px 20px',
                    borderRadius: 16,
                    background: tab === t ? 'var(--accent-warm)' : 'var(--card-bg)',
                    color: 'var(--ink)',
                    boxShadow: 'var(--shadow)',
                  }}
                >
                  {t}
                </button>
              ))}
          </div>
        )}
        {!isKana && <div style={{ margin: '0 auto' }} />}
        <button
          className="tap-target"
          data-testid="btn-reward"
          aria-label="すたんぷちょう"
          onClick={() => navigate({ name: 'reward' })}
          style={{
            fontSize: 30,
            background: 'var(--card-bg)',
            borderRadius: 16,
            boxShadow: 'var(--shadow)',
            width: 64,
            height: 64,
          }}
        >
          📖
        </button>
      </header>

      <div style={{ flex: 1, overflowY: 'auto', marginTop: 12 }}>
        {groups.map((g) => (
          <div
            key={g}
            style={{
              display: 'flex',
              gap: 10,
              marginBottom: 10,
              flexWrap: 'wrap',
            }}
          >
            {chars
              .filter((c) => c.group === g)
              .map((c) => {
                const p = progress[c.id];
                return (
                  <button
                    key={c.id}
                    data-testid={`char-${c.id}`}
                    className="tap-target"
                    onClick={() => {
                      audioManager.sfx('tap');
                      navigate({ name: 'practice', charId: c.id });
                    }}
                    style={{
                      width: 86,
                      height: 86,
                      borderRadius: 18,
                      background: 'var(--card-bg)',
                      boxShadow: 'var(--shadow)',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      justifyContent: 'center',
                      position: 'relative',
                    }}
                  >
                    <span style={{ fontSize: 38, fontWeight: 700, color: 'var(--ink)' }}>
                      {c.char}
                    </span>
                    <span style={{ fontSize: 12, letterSpacing: 1 }}>
                      {[1, 2, 3].map((i) => (
                        <span
                          key={i}
                          style={{ opacity: (p?.bestStars ?? 0) >= i ? 1 : 0.2 }}
                        >
                          ⭐
                        </span>
                      ))}
                    </span>
                    {p?.mastered && (
                      <span
                        style={{ position: 'absolute', top: 2, right: 6, fontSize: 16 }}
                        aria-label="ますたー"
                      >
                        👑
                      </span>
                    )}
                  </button>
                );
              })}
          </div>
        ))}
      </div>
    </div>
  );
}
