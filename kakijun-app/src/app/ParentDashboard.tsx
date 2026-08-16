/**
 * 保護者ダッシュボード (§10.2) + 設定 (§10.3) + データ管理 (§12.6)。
 * この画面は保護者向けなので漢字を使ってよい（付録B）。
 */
import { useEffect, useState } from 'react';
import { useAppStore } from '../store/appStore';
import { characters, listByType } from '../data';
import type { CharType } from '../engine/types';
import { BackButton } from './widgets';

const STATE_COLORS = {
  none: '#eceff1', // まだ
  practicing: '#ffe0b2', // 練習中
  done: '#c8e6c9', // できた
  master: '#ffd54f', // マスター
} as const;

export function ParentDashboard() {
  const navigate = useAppStore((s) => s.navigate);
  const progress = useAppStore((s) => s.progress);
  const settings = useAppStore((s) => s.settings);
  const updateSettings = useAppStore((s) => s.updateSettings);
  const weeklySeconds = useAppStore((s) => s.weeklySeconds);
  const resetTodayTime = useAppStore((s) => s.resetTodayTime);
  const todaySeconds = useAppStore((s) => s.todaySeconds);
  const exportData = useAppStore((s) => s.exportData);
  const importData = useAppStore((s) => s.importData);
  const clearAllData = useAppStore((s) => s.clearAllData);

  const [weekly, setWeekly] = useState(0);
  const [ioText, setIoText] = useState('');
  const [ioMsg, setIoMsg] = useState('');

  useEffect(() => {
    void weeklySeconds().then(setWeekly);
  }, [weeklySeconds, todaySeconds]);

  const practiced = Object.values(progress).filter((p) => p.attempts > 0);
  const totalStars = Object.values(progress).reduce((s, p) => s + p.bestStars, 0);

  // つまずき分析: 書き順ミスの多い文字 上位5つ (§10.2 ★)
  const stumbles = Object.values(progress)
    .map((p) => ({
      p,
      char: characters.find((c) => c.id === p.charId)?.char ?? p.charId,
      orderMistakes: p.mistakeCounts?.order ?? 0, // 旧データ/外部データでも落ちない
    }))
    .filter((x) => x.orderMistakes > 0)
    .sort((a, b) => b.orderMistakes - a.orderMistakes)
    .slice(0, 5);

  function stateOf(charId: string): keyof typeof STATE_COLORS {
    const p = progress[charId];
    if (!p || p.attempts === 0) return 'none';
    if (p.mastered) return 'master';
    if (p.bestStars >= 2) return 'done';
    return 'practicing';
  }

  const sec2min = (s: number) => `${Math.round(s / 60)}分`;

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
        <h1 style={{ fontSize: 24, margin: '0 auto' }}>保護者メニュー</h1>
        <div style={{ width: 64 }} />
      </header>

      <div style={{ flex: 1, overflowY: 'auto', marginTop: 8, fontSize: 15 }}>
        {/* ── 学習サマリー ── */}
        <Section title="学習サマリー">
          <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
            <Metric label="今週の練習時間" value={sec2min(weekly)} />
            <Metric label="今日" value={sec2min(todaySeconds)} />
            <Metric label="練習した文字" value={`${practiced.length}字`} />
            <Metric label="星の合計" value={`⭐${totalStars}`} />
          </div>
        </Section>

        {/* ── 文字別の状況 ── */}
        <Section title="文字別の状況">
          <Legend />
          {(['hiragana', 'katakana', 'number', 'unpitsu'] as CharType[]).map(
            (t) =>
              listByType(t).length > 0 && (
                <div key={t} style={{ marginTop: 8 }}>
                  <div style={{ color: '#78909c', marginBottom: 4 }}>
                    {{ hiragana: 'ひらがな', katakana: 'カタカナ', number: '数字', unpitsu: '運筆' }[t]}
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                    {listByType(t).map((c) => (
                      <span
                        key={c.id}
                        title={c.id}
                        style={{
                          width: 34,
                          height: 34,
                          borderRadius: 8,
                          background: STATE_COLORS[stateOf(c.id)],
                          display: 'inline-flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontSize: 16,
                        }}
                      >
                        {c.char}
                      </span>
                    ))}
                  </div>
                </div>
              ),
          )}
        </Section>

        {/* ── つまずき分析 ── */}
        <Section title="つまずき分析（書き順を間違えやすい文字）">
          {stumbles.length === 0 ? (
            <div style={{ color: '#90a4ae' }}>まだデータがありません</div>
          ) : (
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              {stumbles.map((s) => (
                <div
                  key={s.p.charId}
                  style={{
                    background: '#fff3e0',
                    borderRadius: 12,
                    padding: '8px 14px',
                    textAlign: 'center',
                  }}
                >
                  <div style={{ fontSize: 30, fontWeight: 700 }}>{s.char}</div>
                  <div style={{ fontSize: 13, color: '#e65100' }}>
                    {s.orderMistakes}回
                  </div>
                </div>
              ))}
            </div>
          )}
        </Section>

        {/* ── 設定 (§10.3) ── */}
        <Section title="設定">
          <Row label="判定のきびしさ">
            {(
              [
                ['easy', 'やさしい'],
                ['normal', 'ふつう'],
                ['strict', 'きびしい'],
              ] as const
            ).map(([v, label]) => (
              <Choice
                key={v}
                active={settings.strictness === v}
                onClick={() => updateSettings({ strictness: v })}
              >
                {label}
              </Choice>
            ))}
          </Row>
          <Row label="1回の練習時間の上限">
            {[10, 15, 20, 30, null].map((v) => (
              <Choice
                key={String(v)}
                active={settings.sessionLimitMin === v}
                onClick={() => updateSettings({ sessionLimitMin: v })}
              >
                {v === null ? 'なし' : `${v}分`}
              </Choice>
            ))}
          </Row>
          <Row label="1日の合計上限">
            {[15, 30, 45, 60, null].map((v) => (
              <Choice
                key={String(v)}
                active={settings.dailyLimitMin === v}
                onClick={() => updateSettings({ dailyLimitMin: v })}
              >
                {v === null ? 'なし' : `${v}分`}
              </Choice>
            ))}
          </Row>
          <Row label="音声ガイド">
            <Toggle
              value={settings.voiceEnabled}
              onChange={(v) => updateSettings({ voiceEnabled: v })}
            />
          </Row>
          <Row label="効果音">
            <Toggle
              value={settings.sfxEnabled}
              onChange={(v) => updateSettings({ sfxEnabled: v })}
            />
          </Row>
          <Row label="学習範囲">
            {(
              [
                ['hiragana', 'ひらがな'],
                ['katakana', 'カタカナ'],
                ['number', '数字'],
                ['unpitsu', '運筆'],
              ] as const
            ).map(([t, label]) => (
              <Choice
                key={t}
                active={settings.showTypes[t]}
                onClick={() =>
                  updateSettings({
                    showTypes: { ...settings.showTypes, [t]: !settings.showTypes[t] },
                  })
                }
              >
                {label}
              </Choice>
            ))}
          </Row>
          <Row label="今日の時間制限">
            <button style={btnStyle('#e3f2fd')} onClick={() => resetTodayTime()}>
              リセットして続きを遊べるようにする
            </button>
          </Row>
        </Section>

        {/* ── データ (§10.3, §12.6) ── */}
        <Section title="データのバックアップ">
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <button
              style={btnStyle('#e8f5e9')}
              data-testid="btn-export"
              onClick={async () => {
                try {
                  const json = await exportData();
                  setIoText(json);
                  try {
                    await navigator.clipboard.writeText(json);
                    setIoMsg('エクスポートしました（クリップボードにもコピー済み）');
                  } catch {
                    // iPad Safari はユーザー操作から時間が経つと writeText を拒否する
                    setIoMsg('エクスポートしました。下の欄を長押しでコピーしてください');
                  }
                } catch (e) {
                  setIoMsg(`エクスポートできません: ${String(e)}`);
                }
              }}
            >
              エクスポート
            </button>
            <button
              style={btnStyle('#fff3e0')}
              data-testid="btn-import"
              onClick={async () => {
                try {
                  await importData(ioText);
                  setIoMsg('インポートしました');
                } catch (e) {
                  setIoMsg(`インポートできません: ${String(e)}`);
                }
              }}
            >
              下の欄の JSON をインポート
            </button>
            <button
              style={btnStyle('#ffebee')}
              onClick={async () => {
                if (!confirm('進捗をすべて消します。よろしいですか？')) return;
                try {
                  await clearAllData();
                  setIoMsg('全消去しました');
                } catch (e) {
                  setIoMsg(`消去できません: ${String(e)}`);
                }
              }}
            >
              全消去
            </button>
          </div>
          {ioMsg && <div style={{ marginTop: 6, color: '#2e7d32' }}>{ioMsg}</div>}
          <textarea
            data-testid="io-text"
            value={ioText}
            onChange={(e) => setIoText(e.target.value)}
            placeholder="エクスポートすると JSON がここに出ます。インポートはここに貼り付けてボタンを押してください"
            style={{
              width: '100%',
              height: 120,
              marginTop: 8,
              fontFamily: 'monospace',
              fontSize: 11,
              boxSizing: 'border-box',
              userSelect: 'text',
              WebkitUserSelect: 'text',
            }}
          />
        </Section>
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section
      style={{
        background: 'var(--card-bg)',
        borderRadius: 14,
        boxShadow: 'var(--shadow)',
        padding: 14,
        marginBottom: 12,
      }}
    >
      <h2 style={{ fontSize: 17, margin: '0 0 10px', color: '#546e7a' }}>{title}</h2>
      {children}
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ background: '#f5f7f8', borderRadius: 10, padding: '10px 16px' }}>
      <div style={{ fontSize: 13, color: '#90a4ae' }}>{label}</div>
      <div style={{ fontSize: 22, fontWeight: 700 }}>{value}</div>
    </div>
  );
}

function Legend() {
  return (
    <div style={{ display: 'flex', gap: 12, fontSize: 13, color: '#607d8b' }}>
      {(
        [
          ['none', 'まだ'],
          ['practicing', '練習中'],
          ['done', 'できた'],
          ['master', 'マスター'],
        ] as const
      ).map(([k, label]) => (
        <span key={k} style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
          <span
            style={{
              width: 14,
              height: 14,
              borderRadius: 4,
              background: STATE_COLORS[k],
              display: 'inline-block',
            }}
          />
          {label}
        </span>
      ))}
    </div>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        flexWrap: 'wrap',
        marginBottom: 10,
      }}
    >
      <span style={{ width: 170, color: '#607d8b' }}>{label}</span>
      {children}
    </div>
  );
}

function Choice({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: '7px 14px',
        borderRadius: 10,
        fontSize: 14,
        background: active ? 'var(--accent-warm)' : '#f0f2f3',
        fontWeight: active ? 700 : 400,
      }}
    >
      {children}
    </button>
  );
}

function Toggle({ value, onChange }: { value: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      onClick={() => onChange(!value)}
      style={{
        padding: '7px 18px',
        borderRadius: 10,
        fontSize: 14,
        background: value ? 'var(--accent-warm)' : '#f0f2f3',
      }}
    >
      {value ? 'オン' : 'オフ'}
    </button>
  );
}

function btnStyle(bg: string): React.CSSProperties {
  return { padding: '9px 16px', borderRadius: 10, fontSize: 14, background: bg };
}
