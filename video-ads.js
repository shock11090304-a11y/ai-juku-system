// ==========================================================================
// Video Ads Command Center
// ==========================================================================

// Script duration tab switching
document.querySelectorAll('.script-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    const dur = tab.dataset.duration;
    document.querySelectorAll('.script-tab').forEach(t => t.classList.toggle('active', t === tab));
    document.querySelectorAll('.script-group').forEach(g => {
      g.style.display = g.dataset.duration === dur ? 'grid' : 'none';
    });
  });
});

// Copy script button
document.querySelectorAll('.sc-copy-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const card = btn.closest('.script-card');
    const title = card.querySelector('.sc-title').textContent;
    const duration = card.querySelector('.sc-duration').textContent;
    const tag = card.querySelector('.sc-tag').textContent;
    const shots = [...card.querySelectorAll('.sb-shot')].map(s => {
      const time = s.querySelector('.sb-time').textContent;
      const text = s.textContent.replace(time, '').trim();
      return `${time} ${text}`;
    }).join('\n');
    const full = `🎬 ${title} (${duration}・${tag})\n\n=== 絵コンテ ===\n${shots}`;
    navigator.clipboard.writeText(full).then(() => {
      btn.textContent = '✅ コピー済';
      setTimeout(() => btn.textContent = btn.textContent.includes('📋') ? btn.textContent : '📋 脚本をコピー', 1500);
    });
  });
});

// ==========================================================================
// Product demo auto-player (30秒の自動再生デモ)
// ==========================================================================
const DEMO_FRAMES = [
  { emoji: '🌙', title: '深夜2時...', sub: '娘「もうわかんない…泣」', duration: 3000 },
  { emoji: '📱', title: 'アプリを開く', sub: 'AI学習コーチ塾', duration: 2000 },
  { emoji: '💬', title: '質問を入力', sub: '「関係代名詞のwhichとthatの違いは？」', duration: 3000 },
  { emoji: '🤖', title: 'AIが即回答', sub: '30秒で丁寧な解説を生成', duration: 3000 },
  { emoji: '📊', title: '学習診断も自動', sub: '弱点を自動分析、毎週レポート', duration: 2500 },
  { emoji: '✍️', title: 'AI英作文添削', sub: '無制限に使える', duration: 2500 },
  { emoji: '🎯', title: '志望校別カリキュラム', sub: 'AIが最適経路を30秒で設計', duration: 2500 },
  { emoji: '📷', title: '模試写真から分析', sub: 'Vision AIで自動採点・弱点抽出', duration: 2500 },
  { emoji: '🎓', title: '従来塾の 1/3 の価格', sub: '月 ¥19,800〜', duration: 3000 },
  { emoji: '🎖', title: '🔥 第1期生 100名限定', sub: '3日間 ¥1,980 でお試し', duration: 3500 },
  { emoji: '🚀', title: '今すぐ始めよう', sub: 'ai-juku.jp', duration: 3000 },
];

function playDemo() {
  const modal = document.getElementById('demoModal');
  const viewport = document.getElementById('demoViewport');
  const progressBar = document.getElementById('demoProgress');

  modal.classList.add('show');
  viewport.innerHTML = '';
  progressBar.style.width = '0%';

  // Create frames
  DEMO_FRAMES.forEach((frame, i) => {
    const el = document.createElement('div');
    el.className = 'demo-frame';
    el.dataset.index = i;
    el.innerHTML = `
      <div class="demo-emoji">${frame.emoji}</div>
      <div class="demo-title">${frame.title}</div>
      <div class="demo-sub">${frame.sub}</div>
    `;
    viewport.appendChild(el);
  });

  const totalDuration = DEMO_FRAMES.reduce((sum, f) => sum + f.duration, 0);
  let elapsed = 0;

  // Play frames sequentially
  const playFrame = (index) => {
    if (index >= DEMO_FRAMES.length) {
      // Auto close after final frame
      setTimeout(() => modal.classList.remove('show'), 500);
      return;
    }
    const frames = viewport.querySelectorAll('.demo-frame');
    frames.forEach(f => f.classList.remove('active'));
    frames[index].classList.add('active');

    setTimeout(() => {
      elapsed += DEMO_FRAMES[index].duration;
      progressBar.style.width = `${(elapsed / totalDuration) * 100}%`;
      playFrame(index + 1);
    }, DEMO_FRAMES[index].duration);
  };
  playFrame(0);
}

document.getElementById('playDemoBtn')?.addEventListener('click', playDemo);
document.getElementById('demoModal')?.addEventListener('click', (e) => {
  if (e.target.id === 'demoModal') {
    document.getElementById('demoModal').classList.remove('show');
  }
});
