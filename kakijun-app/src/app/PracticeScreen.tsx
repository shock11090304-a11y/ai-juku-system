/**
 * 練習画面 (§7.3, §7.4)。
 * 判定は pointer イベントごとに実行し、描画は rAF でまとめる (§12.4)。
 */
import { useEffect, useRef, useState } from 'react';
import { useAppStore } from '../store/appStore';
import { getChar, listByType } from '../data';
import { prepareStrokes } from '../engine/loader';
import {
  StrokeMatcher,
  resolveParams,
  type Feedback,
  type MatcherResult,
} from '../engine/strokeMatcher';
import { computeStars } from '../engine/scoring';
import type { GuideLevel, ResampledStroke, Stars } from '../engine/types';
import { CanvasSurface } from '../canvas/CanvasSurface';
import { GuideRenderer } from '../canvas/renderGuide';
import { InkRenderer } from '../canvas/renderInk';
import { attachPointerInput } from '../canvas/pointerInput';
import { audioManager } from '../audio/audioManager';
import { characters } from '../data';
import { computeStamps, earnedKeys } from '../store/rewards';
import { usePracticeWakeLock } from './useWakeLock';
import { BackButton, IconButton, StarRow } from './widgets';

export function PracticeScreen() {
  const screen = useAppStore((s) => s.screen);
  const progress = useAppStore((s) => s.progress);
  const navigate = useAppStore((s) => s.navigate);
  const recordAttempt = useAppStore((s) => s.recordAttempt);
  const setGuideLevel = useAppStore((s) => s.setGuideLevel);
  const tickPracticeTime = useAppStore((s) => s.tickPracticeTime);
  const isTimeUp = useAppStore((s) => s.isTimeUp);
  const remainingSeconds = useAppStore((s) => s.remainingSeconds);

  const charId = screen.name === 'practice' ? screen.charId : '';
  const def = getChar(charId);

  const containerRef = useRef<HTMLDivElement>(null);
  const surfaceRef = useRef<CanvasSurface | null>(null);
  const guideRef = useRef<GuideRenderer | null>(null);
  const inkRef = useRef<InkRenderer | null>(null);
  const matcherRef = useRef<StrokeMatcher | null>(null);
  const strokesRef = useRef<ResampledStroke[]>([]);
  const levelRef = useRef<GuideLevel>(1);

  const [level, setLevel] = useState<GuideLevel>(
    progress[charId]?.guideLevel ?? 1,
  );
  // ★pointer ハンドラはマウント時の effect に closure されるため、
  //   最新の handleResult をここ経由で呼ばないと「つぎのじ」で文字が変わった後も
  //   古い charId の handleResult が呼ばれ、成績が前の文字に記録される
  const handleResultRef = useRef<(r: MatcherResult) => void>(() => {});
  const [celebration, setCelebration] = useState<{
    stars: Stars;
    newStamp: string | null;
  } | null>(null);
  usePracticeWakeLock(); // §12.7 練習中はスリープ防止を試みる（失敗が正常系）
  const celebrationRef = useRef(false);
  const [lowTime, setLowTime] = useState(false);
  levelRef.current = level;

  // ── マウント時: Canvas 3層 + 入力 + rAF ─────────────────────
  useEffect(() => {
    const container = containerRef.current!;
    const surface = new CanvasSurface(container);
    const guide = new GuideRenderer();
    const ink = new InkRenderer();
    surfaceRef.current = surface;
    guideRef.current = guide;
    inkRef.current = ink;

    surface.onLayout = () => {
      guide.renderBackground(surface.bgCtx, surface.size);
    };

    let raf = 0;
    const loop = (now: number) => {
      if (surface.size > 0) {
        guide.renderFrame(surface.guideCtx, surface.size, now);
        ink.render(surface.inkCtx, surface.size);
      }
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);

    const detach = attachPointerInput(surface, {
      onDown: (s) => {
        const m = matcherRef.current;
        if (!m || celebrationRef.current) return;
        const r = m.pointerDown(s.p);
        if (r.type === 'ok') {
          ink.addPoint(s.p.x, s.p.y, s.widthFactor);
        } else {
          handleResultRef.current(r);
        }
      },
      onMove: (s) => {
        const m = matcherRef.current;
        if (!m || !m.state.drawing) return;
        const r = m.pointerMove(s.p);
        if (r.type === 'ok') {
          ink.addPoint(s.p.x, s.p.y, s.widthFactor);
        } else if (r.type === 'feedback') {
          handleResultRef.current(r);
        }
      },
      onUp: () => {
        const m = matcherRef.current;
        if (!m || !m.state.drawing) return;
        handleResultRef.current(m.pointerUp());
      },
      onCancel: () => {
        // エッジスワイプ・通知・パーム乗り換えによる中断。ミス扱いにしない
        matcherRef.current?.cancelStroke();
        inkRef.current?.clearCurrent();
      },
    });

    return () => {
      cancelAnimationFrame(raf);
      detach();
      surface.dispose();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── 文字が変わったとき ───────────────────────────────────
  useEffect(() => {
    // 時間切れ後に新しい文字を始めさせない (§10.4)
    if (isTimeUp()) {
      navigate({ name: 'timeUp' });
      return;
    }
    const startLevel = useAppStore.getState().progress[charId]?.guideLevel ?? 1;
    setLevel(startLevel);
    levelRef.current = startLevel;
    setCelebration(null);
    celebrationRef.current = false;
    startCharacter(startLevel, true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [charId]);

  // ── 練習時間の計測 (§10.4)。画面が見えているときだけ進める ──
  useEffect(() => {
    const iv = setInterval(() => {
      if (document.visibilityState === 'visible') {
        tickPracticeTime();
        const rem = remainingSeconds();
        setLowTime(rem !== null && rem <= 180);
      }
    }, 1000);
    return () => clearInterval(iv);
  }, [tickPracticeTime, remainingSeconds]);

  function startCharacter(lv: GuideLevel, announce: boolean): void {
    const prepared = prepareStrokes(def);
    strokesRef.current = prepared;
    matcherRef.current = new StrokeMatcher(
      prepared,
      resolveParams(useAppStore.getState().settings.strictness, lv),
    );
    const guide = guideRef.current!;
    const surface = surfaceRef.current!;
    guide.setCharacter(prepared, lv);
    inkRef.current!.clearAll();
    if (surface.size > 0) guide.renderBackground(surface.bgCtx, surface.size);
    if (announce) {
      audioManager.playReading(def.id, def.reading);
      audioManager.playStrokeGuide(1, true, false);
    }
    guide.playDemo();
  }

  function handleResult(r: MatcherResult): void {
    const guide = guideRef.current!;
    const ink = inkRef.current!;
    switch (r.type) {
      case 'stroke-ok': {
        ink.commitCurrent();
        guide.strokeIdx = r.nextIdx;
        const done = strokesRef.current[r.committedIdx];
        guide.burst(done.pts[63]);
        audioManager.sfx('pop');
        // 称賛+次の画数を1発話で（別々に積むと速書きで TTS が渋滞する）
        audioManager.playStrokeSuccess(r.nextIdx + 1);
        guide.playDemo();
        break;
      }
      case 'char-complete': {
        ink.commitCurrent();
        const stars = computeStars(r.summary);
        audioManager.sfx('complete');
        audioManager.playPraise();
        const before = earnedKeys(
          computeStamps(characters, useAppStore.getState().progress),
        );
        recordAttempt(charId, stars, r.summary, levelRef.current);
        const after = computeStamps(characters, useAppStore.getState().progress);
        const gained = after.find((s) => s.earned && !before.has(s.key));
        if (gained) audioManager.sfx('stamp');
        celebrationRef.current = true;
        setCelebration({ stars, newStamp: gained?.emoji ?? null });
        break;
      }
      case 'feedback':
        onFeedback(r.feedback);
        break;
      default:
        break;
    }
  }

  // 毎レンダーで最新版に差し替える（マウント時 closure の stale 化対策）
  handleResultRef.current = handleResult;

  function onFeedback(fb: Feedback): void {
    const guide = guideRef.current!;
    const ink = inkRef.current!;
    const m = matcherRef.current!;
    ink.clearCurrent();
    const strokeNumber = m.state.strokeIdx + 1;
    audioManager.playFeedback(fb, strokeNumber);
    switch (fb) {
      case 'start':
        guide.pulseStart();
        break;
      case 'order':
        guide.zoomNumber();
        guide.pulseStart();
        guide.playDemo(); // お手本アニメを1回再生 (§7.4)
        break;
      case 'offpath':
        guide.glowPath();
        break;
      case 'reverse':
        guide.arrowHint();
        break;
      case 'short':
        guide.glowPath();
        break;
    }
    // 3回連続で失敗 → 自動的にガイドを1段階易しくする (§7.4 ★)
    if (m.consecutiveFailures >= 3) {
      m.consecutiveFailures = 0;
      const cur = levelRef.current;
      if (cur > 1) {
        const next = (cur - 1) as GuideLevel;
        setLevel(next);
        levelRef.current = next;
        m.setParams(
          resolveParams(useAppStore.getState().settings.strictness, next),
        );
        guide.level = next;
        const surface = surfaceRef.current!;
        if (surface.size > 0) guide.renderBackground(surface.bgCtx, surface.size);
        guide.playDemo();
        setGuideLevel(charId, next);
        audioManager.sfx('help');
        audioManager.playTogether();
      } else {
        audioManager.playRetryVoice();
      }
    }
  }

  function nextCharId(): string | null {
    const list = listByType(def.type);
    const i = list.findIndex((c) => c.id === def.id);
    return i >= 0 && i + 1 < list.length ? list[i + 1].id : null;
  }

  function closeCelebration(action: 'again' | 'next'): void {
    // 書いている途中で突然止めない: 文字が終わったこのタイミングで発動 (§10.4)
    if (isTimeUp()) {
      navigate({ name: 'timeUp' });
      return;
    }
    if (action === 'again') {
      const lv = useAppStore.getState().progress[charId]?.guideLevel ?? 1;
      setCelebration(null);
      celebrationRef.current = false;
      setLevel(lv);
      levelRef.current = lv;
      startCharacter(lv, false);
    } else {
      const next = nextCharId();
      if (next) navigate({ name: 'practice', charId: next });
      else navigate({ name: 'select', category: def.type });
    }
  }

  const best = progress[charId]?.bestStars ?? 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <header
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          padding: '8px 12px',
        }}
      >
        <BackButton onClick={() => navigate({ name: 'select', category: def.type })} />
        <button
          className="tap-target"
          onClick={() => audioManager.playReading(def.id, def.reading)}
          style={{
            fontSize: 40,
            background: 'none',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}
          aria-label={`${def.reading} をよみあげる`}
        >
          <span style={{ fontWeight: 700 }}>{def.char}</span>
          <span style={{ fontSize: 26 }}>🔊</span>
        </button>
        <div style={{ flex: 1, textAlign: 'center' }}>
          <StarRow stars={best} size={26} />
        </div>
        {/* ガイドレベル表示（小さく） */}
        <div aria-label={`れべる ${level}`} style={{ display: 'flex', gap: 4 }}>
          {[1, 2, 3].map((l) => (
            <span
              key={l}
              style={{
                width: 10,
                height: 10,
                borderRadius: 5,
                background: l <= level ? 'var(--accent-warm)' : '#e0e0e0',
              }}
            />
          ))}
        </div>
        {lowTime && <span style={{ fontSize: 20 }}>⏳</span>}
        <IconButton
          label="やりなおし"
          onClick={() => startCharacter(levelRef.current, false)}
        >
          {/* ゴミ箱ではなく消しゴム (§7.3) */}
          <svg width="34" height="34" viewBox="0 0 34 34">
            <rect
              x="4" y="14" width="20" height="12" rx="3"
              transform="rotate(-25 14 20)"
              fill="#f48fb1" stroke="#ad1457" strokeWidth="1.5"
            />
            <rect
              x="14.5" y="9" width="12" height="12" rx="3"
              transform="rotate(-25 20 15)"
              fill="#fff" stroke="#ad1457" strokeWidth="1.5"
            />
          </svg>
        </IconButton>
      </header>

      <div
        style={{
          flex: 1,
          display: 'flex',
          gap: 12,
          padding: '0 12px 12px',
          minHeight: 0,
        }}
      >
        {/* 絵カード (§7.3) */}
        <aside
          style={{
            width: 180,
            background: 'var(--card-bg)',
            borderRadius: 16,
            boxShadow: 'var(--shadow)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 8,
            alignSelf: 'center',
            padding: 16,
          }}
        >
          <SampleCard />
        </aside>

        {/* 描画エリア（正方形 §5.2） */}
        <div
          style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            minWidth: 0,
            minHeight: 0,
          }}
        >
          <div
            ref={containerRef}
            data-testid="practice-canvas"
            style={{
              position: 'relative',
              height: '100%',
              maxWidth: '100%',
              aspectRatio: '1 / 1',
              background: '#fff',
              borderRadius: 16,
              boxShadow: 'var(--shadow)',
              overflow: 'hidden',
            }}
          />
        </div>
      </div>

      {celebration && (
        <CelebrationOverlay
          stars={celebration.stars}
          newStamp={celebration.newStamp}
          onAgain={() => closeCelebration('again')}
          onNext={() => closeCelebration('next')}
        />
      )}
    </div>
  );

  function SampleCard() {
    if (def.type === 'number') {
      const n = parseInt(def.char, 10);
      return (
        <>
          <div style={{ fontSize: 30, lineHeight: 1.3, textAlign: 'center' }}>
            {n === 0 ? '🍽️' : '🍎'.repeat(Math.min(n, 10))}
          </div>
          <div style={{ fontSize: 24 }}>{def.reading}</div>
          <SpeakButton text={def.reading} />
        </>
      );
    }
    if (!def.sample) return <div style={{ fontSize: 56 }}>✏️</div>;
    const emoji = def.sample.image.startsWith('emoji:')
      ? def.sample.image.slice(6)
      : '🖼️';
    return (
      <>
        <div style={{ fontSize: 72 }}>{emoji}</div>
        <div style={{ fontSize: 26 }}>{def.sample.word}</div>
        <SpeakButton text={def.sample.word} audioFile={def.sample.audio} />
      </>
    );
  }

  function SpeakButton({ text, audioFile }: { text: string; audioFile?: string }) {
    return (
      <button
        className="tap-target"
        style={{ fontSize: 28, background: 'none' }}
        onClick={() => audioManager.playWord(audioFile, text)}
        aria-label={`${text} をよみあげる`}
      >
        🔊
      </button>
    );
  }
}

/** 花丸 + 星 + もういっかい / つぎのじ (§7.3)。演出は3秒以内 (§9.2) */
function CelebrationOverlay({
  stars,
  newStamp,
  onAgain,
  onNext,
}: {
  stars: Stars;
  newStamp: string | null;
  onAgain: () => void;
  onNext: () => void;
}) {
  return (
    <div
      data-testid="celebration"
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(255,253,247,0.92)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 16,
        zIndex: 100,
        animation: 'fadein 0.3s',
      }}
    >
      <div style={{ fontSize: 110, animation: 'popin 0.6s' }}>💮</div>
      <StarRow stars={stars} size={44} animated />
      {newStamp && (
        <div
          data-testid="new-stamp"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            fontSize: 26,
            animation: 'popin 0.6s 0.8s backwards',
          }}
        >
          <span
            style={{
              fontSize: 54,
              background: '#fff8e1',
              border: '4px solid var(--accent-warm)',
              borderRadius: '50%',
              width: 90,
              height: 90,
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {newStamp}
          </span>
          すたんぷ げっと！
        </div>
      )}
      <div style={{ display: 'flex', gap: 24, marginTop: 12 }}>
        <button
          className="tap-target"
          data-testid="btn-again"
          onClick={onAgain}
          style={celebBtn('#e3f2fd')}
        >
          <span style={{ fontSize: 34 }}>🔁</span>
          <span style={{ fontSize: 18 }}>もういっかい</span>
        </button>
        <button
          className="tap-target"
          data-testid="btn-next"
          onClick={onNext}
          style={celebBtn('#fff3e0')}
        >
          <span style={{ fontSize: 34 }}>➡️</span>
          <span style={{ fontSize: 18 }}>つぎのじ</span>
        </button>
      </div>
    </div>
  );
}

function celebBtn(bg: string): React.CSSProperties {
  return {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: 4,
    padding: '14px 26px',
    borderRadius: 18,
    background: bg,
    boxShadow: 'var(--shadow)',
  };
}
