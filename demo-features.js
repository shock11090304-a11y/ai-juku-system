// ==========================================================================
// 実機能デモ — 各機能を美しいビジュアルモックで紹介（iframe非依存・軽量）
// ==========================================================================

const FRAMES = [
  {
    key: 'tutor',
    title: '24時間 AI チューター',
    subtitle: '深夜でも日曜日でも質問即答',
    duration: 10000,
    desc: 'いつでも、どこでも、わからない問題をAIが即解説。深夜2時でも、日曜日でも、勉強が止まりません。',
    stats: [
      { num: '24h', label: '応答時間' },
      { num: '30秒', label: '解答生成' },
    ],
    wow: '💡 <strong>ここがすごい:</strong> 塾講師なら週2回しか質問できないが、これは年中無休24時間対応。',
    linkHash: 'tab-tutor',
    mockup: 'tutor',
  },
  {
    key: 'diagnostic',
    title: '📷 模試 Vision AI',
    subtitle: '写真から自動分析',
    duration: 11000,
    desc: '模試結果の写真を撮るだけで、AIが自動でスコアを読み取り、弱点を特定、次週の学習プランまで提案。',
    stats: [
      { num: '30秒', label: '写真→分析' },
      { num: '95%', label: '読取精度' },
    ],
    wow: '💡 <strong>ここがすごい:</strong> 全統/駿台/河合塾など主要模試に対応。手入力ゼロ。',
    linkHash: 'tab-diagnostic',
    mockup: 'moshi',
  },
  {
    key: 'problems',
    title: '🧪 AI問題自動生成',
    subtitle: '弱点から20問を瞬時に',
    duration: 10000,
    desc: '単元を選ぶだけで、オリジナル問題が20問一気に生成されます。解答・解説・学習ポイント付き。',
    stats: [
      { num: '20問', label: '1クリックで' },
      { num: '無制限', label: '月間生成数' },
    ],
    wow: '💡 <strong>ここがすごい:</strong> 同じ単元で何度作っても毎回違う問題。市販問題集を買う必要がなくなる。',
    linkHash: 'tab-problems',
    mockup: 'problems',
  },
  {
    key: 'curriculum',
    title: '🎯 志望校別カリキュラム',
    subtitle: '30秒で年間計画完成',
    duration: 9000,
    desc: '志望校と現在地を入力すれば、合格までの年間計画が30秒で完成。教材・時間配分まで具体的に。',
    stats: [
      { num: '30秒', label: 'カリキュラム生成' },
      { num: '1/1', label: '個別最適化' },
    ],
    wow: '💡 <strong>ここがすごい:</strong> 通常は学習コンサルが数時間かけて作る年間計画が即完成。',
    linkHash: 'tab-curriculum',
    mockup: 'curriculum',
  },
  {
    key: 'essay',
    title: '✍️ AI英作文・記述添削',
    subtitle: '10倍の添削量',
    duration: 9000,
    desc: '答案を入力して10秒待つだけで、文法・語彙・論理構造まで詳細な添削が返ってきます。',
    stats: [
      { num: '10倍', label: '添削量' },
      { num: '即時', label: '返却' },
    ],
    wow: '💡 <strong>ここがすごい:</strong> 英検合格者の添削量と合格率は比例。AIで合格率 12% → 81% の上昇実績。',
    linkHash: 'tab-essay',
    mockup: 'essay',
  },
  {
    key: 'speaking',
    title: '🎙 スピーキング練習（音声AI）',
    subtitle: '音声認識+AI採点',
    duration: 9000,
    desc: '英検2次試験・大学入試面接・TOEFLのスピーキング対策。AIが発音・文法・流暢さを3軸で採点。',
    stats: [
      { num: '3軸', label: 'AI採点' },
      { num: '6モード', label: '練習形式' },
    ],
    wow: '💡 <strong>ここがすごい:</strong> オンライン英会話は1コマ¥1,000だが、これは月額内で無制限。',
    linkHash: 'tab-speaking',
    mockup: 'speaking',
  },
  {
    key: 'textbook',
    title: '📚 AI教材自動生成',
    subtitle: '駿台テキスト級を数分で',
    duration: 11000,
    desc: '単元を指定するだけで、駿台テキスト級の本格教材を数分で作成。PDF出力・印刷対応。',
    stats: [
      { num: '数分', label: '10-20ページ' },
      { num: '¥0', label: '追加料金' },
    ],
    wow: '💡 <strong>ここがすごい:</strong> 市販問題集¥2,000〜5,000が無限に作れる。',
    linkUrl: 'textbook-generator.html',
    mockup: 'textbook',
  },
  {
    key: 'parent',
    title: '👨‍👩‍👧 保護者レポート',
    subtitle: 'LINE週次配信で安心',
    duration: 10000,
    desc: 'お子様の学習進捗を毎週日曜にLINE配信。AIが生徒データを読み取り、保護者向けに分かりやすく要約。',
    stats: [
      { num: '毎週日曜', label: '自動配信' },
      { num: '95%', label: '継続率' },
    ],
    wow: '💡 <strong>ここがすごい:</strong> 「ちゃんと勉強してる？」と聞く必要がなくなる。',
    linkHash: 'tab-parent',
    mockup: 'parent',
  },
];

// ==========================================================================
// Visual mockups per feature
// ==========================================================================
const MOCKUPS = {
  tutor: () => `
    <div class="mock-app mock-tutor">
      <div class="mock-toolbar">
        <div class="mock-logo">🎓 AI学習コーチ塾</div>
        <div class="mock-badge-live">🟢 AI稼働中</div>
      </div>
      <div class="mock-chat">
        <div class="mock-msg user-msg anim-fade-1">
          <div class="mock-avatar">👤</div>
          <div class="mock-bubble">関係代名詞のwhich と that の使い分けがわかりません</div>
        </div>
        <div class="mock-msg ai-msg anim-fade-2">
          <div class="mock-avatar">🤖</div>
          <div class="mock-bubble">
            <div class="mock-typing">
              <h4>【基本ルール】</h4>
              <p>・<strong>which</strong>: モノや動物が先行詞の時</p>
              <p>・<strong>that</strong>: モノ・人・どちらにも使える（最上級・序数の後は特に好まれる）</p>
              <h4>【例文】</h4>
              <p>The book <strong>which/that</strong> I read yesterday was interesting.</p>
              <p>This is the best movie <strong>that</strong> I've ever seen.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  moshi: () => `
    <div class="mock-app mock-moshi">
      <div class="mock-toolbar">
        <div class="mock-logo">📊 学習診断</div>
      </div>
      <div class="mock-moshi-flow">
        <div class="mock-upload anim-slide-up">
          <div class="mock-upload-icon">📷</div>
          <div>模試の写真をアップロード</div>
        </div>
        <div class="mock-arrow-down anim-bounce">↓</div>
        <div class="mock-analyzing anim-fade-2">
          🔍 AI解析中...
          <div class="mock-spinner"></div>
        </div>
        <div class="mock-result anim-fade-3">
          <div class="mock-result-title">✅ 解析完了</div>
          <div class="mock-result-grid">
            <div><strong>英語:</strong> 145/200（偏差値65）</div>
            <div><strong>数学:</strong> 128/200（偏差値58）</div>
            <div><strong>国語:</strong> 156/200（偏差値68）</div>
          </div>
          <div class="mock-weak">⚠️ 弱点: 数学の二次関数・場合の数</div>
        </div>
      </div>
    </div>
  `,
  problems: () => `
    <div class="mock-app mock-problems">
      <div class="mock-toolbar">
        <div class="mock-logo">🧪 AI問題自動生成</div>
      </div>
      <div class="mock-form anim-fade-1">
        <div class="mock-field">単元: <strong>関係代名詞</strong></div>
        <div class="mock-field">難易度: <strong>標準</strong> / 数: <strong>10問</strong></div>
        <div class="mock-gen-btn">🎲 問題を生成</div>
      </div>
      <div class="mock-arrow-down anim-bounce">↓</div>
      <div class="mock-problems-output anim-fade-3">
        <div class="mock-problem">
          <strong>問題1</strong><br>
          次の空所に入る最も適切な関係代名詞を選びなさい。<br>
          <em>The book ( ) I borrowed from the library was interesting.</em>
        </div>
        <div class="mock-problem">
          <strong>問題2</strong><br>
          次の2文を関係代名詞で1つに。<br>
          <em>This is the teacher. He taught me English.</em>
        </div>
        <div class="mock-more">+ 8問 生成中...</div>
      </div>
    </div>
  `,
  curriculum: () => `
    <div class="mock-app mock-curriculum">
      <div class="mock-toolbar">
        <div class="mock-logo">🎯 カリキュラム自動生成</div>
      </div>
      <div class="mock-input-card anim-fade-1">
        <div>志望校: <strong>東京大学 文科一類</strong></div>
        <div>現状: 偏差値62</div>
        <div>試験日: 2027年2月</div>
      </div>
      <div class="mock-arrow-down anim-bounce">↓</div>
      <div class="mock-timeline anim-fade-3">
        <div class="mock-phase"><span class="phase-label">フェーズ1</span> 基礎固め (3ヶ月)</div>
        <div class="mock-phase"><span class="phase-label">フェーズ2</span> 標準演習 (4ヶ月)</div>
        <div class="mock-phase"><span class="phase-label">フェーズ3</span> 過去問演習 (5ヶ月)</div>
        <div class="mock-weekly">週間: 月水金=英語 / 火木=数学 / 土=過去問</div>
      </div>
    </div>
  `,
  essay: () => `
    <div class="mock-app mock-essay">
      <div class="mock-toolbar">
        <div class="mock-logo">✍️ AI英作文添削</div>
      </div>
      <div class="mock-essay-grid">
        <div class="mock-left anim-fade-1">
          <h4>生徒の答案</h4>
          <p>I think uniforms is good because students look same.</p>
          <p>First reason, it is cheaper...</p>
        </div>
        <div class="mock-arrow-right anim-bounce">→</div>
        <div class="mock-right anim-fade-3">
          <h4>AI添削結果</h4>
          <div class="essay-score">📊 総合: 16/20点</div>
          <div class="essay-fix"><span class="fix-wrong">uniforms is</span> → <span class="fix-right">uniforms are</span></div>
          <div class="essay-fix"><span class="fix-wrong">look same</span> → <span class="fix-right">look the same</span></div>
          <div class="essay-tip">💡 三単現のs/be動詞の一致に注意</div>
        </div>
      </div>
    </div>
  `,
  speaking: () => `
    <div class="mock-app mock-speaking">
      <div class="mock-toolbar">
        <div class="mock-logo">🎙 スピーキング練習</div>
      </div>
      <div class="mock-speaking-flow">
        <div class="mock-mic anim-pulse">🎤</div>
        <div class="mock-ai-prompt anim-fade-1">
          <strong>🤖 AI:</strong> Tell me about your hobby.
        </div>
        <div class="mock-transcript anim-fade-2">
          <em>"My hobby is playing tennis. I started when I was..."</em>
        </div>
        <div class="mock-score-grid anim-fade-3">
          <div class="score-ring"><div class="score-num">72</div><div class="score-label">発音</div></div>
          <div class="score-ring"><div class="score-num">68</div><div class="score-label">文法</div></div>
          <div class="score-ring"><div class="score-num">75</div><div class="score-label">流暢さ</div></div>
        </div>
      </div>
    </div>
  `,
  textbook: () => `
    <div class="mock-app mock-textbook">
      <div class="mock-toolbar">
        <div class="mock-logo">📚 テキスト教材生成</div>
      </div>
      <div class="mock-tb-input anim-fade-1">
        <div>単元: <strong>関係代名詞</strong></div>
        <div>分量: <strong>A4で5-8ページ</strong></div>
        <div>要素: 導入 / 基本事項 / 例題 / 演習 / 解答 / まとめ</div>
      </div>
      <div class="mock-arrow-down anim-bounce">↓</div>
      <div class="mock-tb-output anim-fade-3">
        <h3>📖 関係代名詞 完全マスター</h3>
        <h4>§1 はじめに</h4>
        <p>関係代名詞は英文法の中でも特に重要な...</p>
        <h4>§2 基本事項</h4>
        <p>まずは3つの要素を押さえましょう...</p>
        <div class="tb-tip">💡 ここがポイント</div>
        <h4>§3 例題</h4>
        <div>問題1: ...</div>
        <div class="mock-more">+ さらに詳細な教材が続く（駿台テキスト級）</div>
      </div>
    </div>
  `,
  parent: () => `
    <div class="mock-app mock-parent">
      <div class="mock-line-header">
        <div class="line-avatar">🎓</div>
        <div>
          <div class="line-name">AI学習コーチ塾</div>
          <div class="line-status">公式アカウント</div>
        </div>
      </div>
      <div class="mock-line-chat">
        <div class="line-bubble anim-fade-1">
          <strong>📊 太郎さんの今週のレポート</strong><br><br>
          🔥 学習時間: <strong>12.5時間</strong> (+2.5h)<br>
          💯 平均正答率: <strong>78%</strong> (+5%)<br>
          💬 AI質問数: <strong>47回</strong><br><br>
          ✨ 成長エピソード: 英検準1級の過去問で初めて合格ラインに到達！
        </div>
        <div class="line-time anim-fade-2">日曜 20:00 自動配信</div>
      </div>
    </div>
  `,
};

let currentIndex = 0;
let timer = null;
let startTime = 0;
let isPlaying = true;

function getSeatsLeft() {
  const count = parseInt(localStorage.getItem('ai_juku_founder_count') || '32');
  return Math.max(0, 100 - count);
}

function renderChips() {
  const container = document.getElementById('featureChips');
  container.innerHTML = FRAMES.map((f, i) =>
    `<button class="fc-chip ${i === currentIndex ? 'active' : ''}" data-i="${i}">${f.title}</button>`
  ).join('');
  container.querySelectorAll('.fc-chip').forEach(chip => {
    chip.addEventListener('click', () => goTo(parseInt(chip.dataset.i)));
  });
}

function renderFrame(i) {
  const frame = FRAMES[i];
  const viewport = document.getElementById('mockViewport');

  // Crossfade mockup
  viewport.classList.add('switching');
  setTimeout(() => {
    viewport.innerHTML = MOCKUPS[frame.mockup] ? MOCKUPS[frame.mockup]() : '';
    viewport.classList.remove('switching');
  }, 200);

  // Narration panel
  document.getElementById('npTitle').textContent = frame.title;
  document.getElementById('npDesc').textContent = frame.desc;

  const statsEl = document.getElementById('npStats');
  statsEl.innerHTML = frame.stats.map(s =>
    `<div class="np-stat"><div class="nps-num">${s.num}</div><div class="nps-label">${s.label}</div></div>`
  ).join('');

  document.getElementById('npWow').innerHTML = frame.wow;

  // Badge & title
  document.getElementById('featureBadge').textContent = `🎓 ${i + 1}/${FRAMES.length}`;
  document.getElementById('currentFrame').textContent = i + 1;
  document.getElementById('frameTitle').textContent = frame.title;

  // Update "実際に使う" link
  const useBtn = document.getElementById('useRealBtn');
  if (useBtn) {
    useBtn.href = frame.linkUrl || (frame.linkHash ? `index.html#${frame.linkHash}` : 'index.html');
  }

  // Update chips
  document.querySelectorAll('.fc-chip').forEach((c, idx) => {
    c.classList.toggle('active', idx === i);
  });

  // Update seats counter
  const sr = document.getElementById('seatsRemaining');
  if (sr) sr.textContent = getSeatsLeft();
}

function startTimer() {
  clearInterval(timer);
  startTime = Date.now();
  const duration = FRAMES[currentIndex].duration;
  const progressBar = document.getElementById('dpBar');
  progressBar.style.width = '0%';

  timer = setInterval(() => {
    if (!isPlaying) return;
    const elapsed = Date.now() - startTime;
    const pct = Math.min(100, (elapsed / duration) * 100);
    progressBar.style.width = `${pct}%`;
    if (elapsed >= duration) {
      clearInterval(timer);
      next();
    }
  }, 50);
}

function next() {
  currentIndex = (currentIndex + 1) % FRAMES.length;
  renderFrame(currentIndex);
  if (isPlaying) startTimer();
}

function prev() {
  currentIndex = (currentIndex - 1 + FRAMES.length) % FRAMES.length;
  renderFrame(currentIndex);
  if (isPlaying) startTimer();
}

function goTo(i) {
  currentIndex = i;
  renderFrame(currentIndex);
  if (isPlaying) startTimer();
}

function togglePlay() {
  isPlaying = !isPlaying;
  document.getElementById('playBtn').textContent = isPlaying ? '⏸' : '▶';
  if (isPlaying) {
    startTimer();
  } else {
    clearInterval(timer);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('totalFrames').textContent = FRAMES.length;
  renderChips();
  renderFrame(0);
  startTimer();

  document.getElementById('playBtn').addEventListener('click', togglePlay);
  document.getElementById('nextBtn').addEventListener('click', next);
  document.getElementById('prevBtn').addEventListener('click', prev);
  document.getElementById('fullscreenBtn').addEventListener('click', () => {
    if (!document.fullscreenElement) document.documentElement.requestFullscreen();
    else document.exitFullscreen();
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowRight' || e.key === ' ') next();
    else if (e.key === 'ArrowLeft') prev();
    else if (e.key === 'p' || e.key === 'P') togglePlay();
  });
});
