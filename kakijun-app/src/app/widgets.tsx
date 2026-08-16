/**
 * 画面共通の小物。戻るボタンは常に左上・同じ絵 (§11-4)。
 */
import type { ReactNode } from 'react';
import type { Stars } from '../engine/types';

export function BackButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      className="tap-target"
      data-testid="btn-back"
      onClick={onClick}
      aria-label="もどる"
      style={{
        background: 'var(--card-bg)',
        borderRadius: 16,
        boxShadow: 'var(--shadow)',
        fontSize: 30,
        width: 64,
        height: 64,
      }}
    >
      <svg width="34" height="34" viewBox="0 0 34 34" style={{ verticalAlign: 'middle' }}>
        <path
          d="M22 6 L10 17 L22 28"
          fill="none"
          stroke="var(--ink)"
          strokeWidth="4.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </button>
  );
}

export function IconButton({
  label,
  onClick,
  children,
}: {
  label: string;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      className="tap-target"
      onClick={onClick}
      aria-label={label}
      style={{
        background: 'var(--card-bg)',
        borderRadius: 16,
        boxShadow: 'var(--shadow)',
        width: 64,
        height: 64,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      {children}
    </button>
  );
}

export function StarRow({
  stars,
  size,
  animated = false,
}: {
  stars: Stars;
  size: number;
  animated?: boolean;
}) {
  return (
    <span
      aria-label={`ほし ${stars}こ`}
      style={{ fontSize: size, letterSpacing: 4, whiteSpace: 'nowrap' }}
    >
      {[1, 2, 3].map((i) => (
        <span
          key={i}
          style={{
            opacity: i <= stars ? 1 : 0.25,
            display: 'inline-block',
            animation:
              animated && i <= stars ? `popin 0.5s ${i * 0.25}s backwards` : undefined,
          }}
        >
          ⭐
        </span>
      ))}
    </span>
  );
}
