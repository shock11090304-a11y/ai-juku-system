/**
 * ホーム画面 (§7.1)。大きな絵タイル4つ + 右上に小さな歯車（保護者画面入口）。
 * 文字が読めなくても絵と音で選べるようにする (§11-2)。
 */
import { useAppStore } from '../store/appStore';
import { listByType } from '../data';
import { audioManager } from '../audio/audioManager';
import type { CharType } from '../engine/types';

const TILES: {
  type: CharType;
  glyph: string;
  emoji: string;
  label: string;
  bg: string;
}[] = [
  { type: 'hiragana', glyph: 'あ', emoji: '🐜', label: 'ひらがな', bg: '#ffe0b2' },
  { type: 'katakana', glyph: 'ア', emoji: '🦁', label: 'カタカナ', bg: '#b3e5fc' },
  { type: 'number', glyph: '123', emoji: '🍎', label: 'すうじ', bg: '#c8e6c9' },
  { type: 'unpitsu', glyph: '〜', emoji: '🚗', label: 'せんの れんしゅう', bg: '#f8bbd0' },
];

export function HomeScreen() {
  const navigate = useAppStore((s) => s.navigate);
  const settings = useAppStore((s) => s.settings);

  return (
    <div
      style={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        padding: 16,
        boxSizing: 'border-box',
      }}
    >
      <header style={{ display: 'flex', alignItems: 'center' }}>
        <h1 style={{ fontSize: 30, margin: '0 auto', color: 'var(--ink)' }}>
          ✏️ かきじゅん れんしゅう
        </h1>
        {/* 目立たない小さな歯車 (§7.1)。誤タップしても掛け算ゲートで止まる */}
        <button
          data-testid="btn-gear"
          onClick={() => navigate({ name: 'parentGate' })}
          aria-label="おうちのひとの がめん"
          style={{
            background: 'none',
            fontSize: 20,
            opacity: 0.45,
            width: 44,
            height: 44,
          }}
        >
          ⚙️
        </button>
      </header>

      <div
        style={{
          flex: 1,
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 16,
          marginTop: 12,
          minHeight: 0,
        }}
      >
        {TILES.filter((t) => settings.showTypes[t.type]).map((t) => {
          const enabled = listByType(t.type).length > 0;
          return (
            <button
              key={t.type}
              data-testid={`tile-${t.type}`}
              className="tap-target"
              disabled={!enabled}
              onClick={() => {
                audioManager.sfx('tap');
                navigate({ name: 'select', category: t.type });
              }}
              style={{
                background: enabled ? t.bg : '#eceff1',
                borderRadius: 24,
                boxShadow: 'var(--shadow)',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 8,
                opacity: enabled ? 1 : 0.4,
              }}
            >
              <div style={{ fontSize: 64, fontWeight: 700, color: 'var(--ink)' }}>
                {t.glyph} <span style={{ fontSize: 54 }}>{t.emoji}</span>
              </div>
              <div style={{ fontSize: 24, color: 'var(--ink)' }}>{t.label}</div>
            </button>
          );
        })}
      </div>
      {/* 配信中のビルド刻印。古いキャッシュを掴んでいないかを画面から判別するため */}
      <div
        data-testid="build-stamp"
        style={{
          position: 'fixed',
          right: 8,
          bottom: 6,
          fontSize: 11,
          color: 'rgba(0,0,0,0.28)',
          userSelect: 'text',
        }}
      >
        {__BUILD_STAMP__}
      </div>
    </div>
  );
}
