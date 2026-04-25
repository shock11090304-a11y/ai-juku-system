/**
 * 合格者SNS連携 (Success Stories)
 *
 * 機能:
 *  - 合格体験談の投稿・閲覧
 *  - 大学・学部・学習時間・偏差値推移などの構造化情報
 *  - SNSシェア (X / LINE) のためのテンプレート生成
 *  - フィルタ (志望校、偏差値帯、現役/浪人)
 *
 * デフォルト: シード(seed)合格者データを内蔵 (空のサービスを避けるため)
 */
(function () {
  'use strict';
  const LS_STORIES = 'ai_juku_success_stories__user_posts';

  const SEED_STORIES = [
    {
      id: 'seed_001',
      name: '山田 (仮名)',
      grade: '現役',
      year: 2026,
      school: '早稲田大学 政治経済学部',
      schoolBefore: '都内私立高校',
      deviationStart: 56,
      deviationEnd: 68,
      studyHours: 1200,
      mainSubjects: ['英語', '日本史', '現代文'],
      story: '高2の冬から塾を変え、AI個別指導で1日2時間×毎日続けました。エビングハウス自動復習で英単語の定着率が劇的に上がり、半年で偏差値が10上がりました。秋以降は過去問演習に集中し、滑り止めもしっかり押さえて第一志望に合格。',
      advice: '毎日コツコツの積み重ねを過信しないでください。自分が何を理解できていて、何ができていないかを把握することが最重要です。',
      seed: true,
    },
    {
      id: 'seed_002',
      name: '佐藤 (仮名)',
      grade: '浪人',
      year: 2026,
      school: '東北大学 工学部',
      schoolBefore: '地方公立高校',
      deviationStart: 60,
      deviationEnd: 67,
      studyHours: 2400,
      mainSubjects: ['数学', '物理', '化学'],
      story: '現役時代は東北大に2点足らず不合格。1年間予備校に通いながら、AI塾は弱点補強用に併用しました。「躓きセンサー」が三角関数の盲点を指摘してくれて、夏前に基礎をやり直したのが転機でした。',
      advice: '浪人は「同じ勉強を繰り返さない」が鉄則。前年と同じ参考書を同じやり方で解いても伸びません。自分の弱点を客観的に分析できるツールを活用してください。',
      seed: true,
    },
    {
      id: 'seed_003',
      name: '鈴木 (仮名)',
      grade: '現役',
      year: 2026,
      school: '慶應義塾大学 経済学部',
      schoolBefore: '都内中高一貫校',
      deviationStart: 65,
      deviationEnd: 72,
      studyHours: 1800,
      mainSubjects: ['英語', '数学', '小論文'],
      story: '中学3年から英語に注力していたので英語は得意でしたが、数学が伸び悩んでいました。AI塾の適応難易度機能で、自分のレベルにピッタリ合った問題を解き続けられたのが良かったです。',
      advice: '得意科目で稼ぐより、苦手科目を平均レベルまで引き上げる方が合計点を伸ばしやすい。これに気付くのが遅れると後悔します。',
      seed: true,
    },
    {
      id: 'seed_004',
      name: '田中 (仮名)',
      grade: '現役',
      year: 2026,
      school: '同志社大学 法学部',
      schoolBefore: '関西公立高校',
      deviationStart: 52,
      deviationEnd: 60,
      studyHours: 1500,
      mainSubjects: ['英語', '世界史', '国語'],
      story: 'もともと公募推薦で滑り止めを確保した上で、一般入試で同志社に挑戦。AI塾の過去問類題生成で同志社の出題傾向に合わせた演習ができ、本番で得意な世界史を9割取れました。',
      advice: '滑り止めは「絶対に合格できる」という心の余裕を生みます。本命にチャレンジするなら必ず確保してください。',
      seed: true,
    },
    {
      id: 'seed_005',
      name: '高橋 (仮名)',
      grade: '現役',
      year: 2026,
      school: '明治大学 商学部',
      schoolBefore: '都内私立高校',
      deviationStart: 50,
      deviationEnd: 58,
      studyHours: 1100,
      mainSubjects: ['英語', '日本史', '国語'],
      story: '部活引退後の高3夏から本格的に受験勉強開始。短期間だったので「何をやらないか」を決めるのに苦労しましたが、AI塾の苦手分析で勉強の優先順位を立てられたのが助かりました。',
      advice: '時間が無い時こそ、闇雲に手を広げず「絞る」勇気が大事。すべての科目を伸ばそうとして全部中途半端になるのが一番のリスクです。',
      seed: true,
    },
  ];

  function _read() {
    try { return JSON.parse(localStorage.getItem(LS_STORIES) || '[]'); }
    catch { return []; }
  }
  function _write(stories) {
    try { localStorage.setItem(LS_STORIES, JSON.stringify(stories)); }
    catch (e) { console.warn('SuccessStories storage write failed:', e); }
  }

  function getAllStories(includeSeed = true) {
    const user = _read();
    return includeSeed ? [...user, ...SEED_STORIES] : user;
  }

  function addStory(opts) {
    const stories = _read();
    const story = {
      id: 'user_' + Date.now() + '_' + Math.floor(Math.random() * 9999),
      name: opts.name || '匿名',
      grade: opts.grade || '現役',
      year: opts.year || new Date().getFullYear(),
      school: opts.school || '',
      schoolBefore: opts.schoolBefore || '',
      deviationStart: parseInt(opts.deviationStart) || null,
      deviationEnd: parseInt(opts.deviationEnd) || null,
      studyHours: parseInt(opts.studyHours) || null,
      mainSubjects: opts.mainSubjects || [],
      story: opts.story || '',
      advice: opts.advice || '',
      createdAt: new Date().toISOString(),
      seed: false,
    };
    stories.unshift(story);
    _write(stories);
    return story;
  }

  function deleteStory(id) {
    const stories = _read().filter(s => s.id !== id);
    _write(stories);
  }

  function filterStories(filter) {
    const all = getAllStories();
    return all.filter(s => {
      if (filter.school && !s.school.includes(filter.school)) return false;
      if (filter.grade && filter.grade !== 'all' && s.grade !== filter.grade) return false;
      if (filter.subject && !(s.mainSubjects || []).includes(filter.subject)) return false;
      return true;
    });
  }

  function buildShareText(story) {
    const gain = (story.deviationStart && story.deviationEnd)
      ? ` (偏差値${story.deviationStart}→${story.deviationEnd})`
      : '';
    return `🎓 ${story.school} 合格${gain}！
${story.story.slice(0, 80)}${story.story.length > 80 ? '...' : ''}
#AI塾 #合格体験記 #大学受験`;
  }

  function _shareLine(story) {
    const text = buildShareText(story);
    const url = `https://line.me/R/msg/text/?${encodeURIComponent(text + '\n' + window.location.href)}`;
    window.open(url, '_blank');
  }
  function _shareTwitter(story) {
    const text = buildShareText(story);
    const url = `https://x.com/intent/post?text=${encodeURIComponent(text)}&url=${encodeURIComponent(window.location.href)}`;
    window.open(url, '_blank');
  }

  function renderStoryCard(s) {
    const gain = (s.deviationStart && s.deviationEnd)
      ? `<span style="font-size:0.78rem;color:#34d399;background:rgba(16,185,129,0.1);padding:0.2rem 0.5rem;border-radius:4px;">偏差値 ${s.deviationStart} → ${s.deviationEnd} (+${s.deviationEnd - s.deviationStart})</span>`
      : '';
    const subjects = (s.mainSubjects || []).map(sub =>
      `<span style="font-size:0.72rem;background:rgba(99,102,241,0.15);color:#a78bfa;padding:0.15rem 0.45rem;border-radius:4px;margin-right:0.25rem;">${sub}</span>`
    ).join('');
    return `
      <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1);border-left:4px solid #f59e0b;border-radius:12px;padding:1rem;margin-bottom:0.8rem;">
        <div style="display:flex;justify-content:space-between;align-items:start;gap:0.5rem;flex-wrap:wrap;">
          <div style="flex:1;min-width:200px;">
            <div style="font-weight:800;color:#fbbf24;font-size:1.05rem;">🎓 ${s.school}</div>
            <div style="font-size:0.82rem;color:#a1a1aa;margin:0.25rem 0;">${s.year}年 · ${s.grade} · ${s.name}${s.schoolBefore ? ` · ${s.schoolBefore}` : ''}</div>
            <div style="margin:0.4rem 0;">${gain} ${s.studyHours ? `<span style="font-size:0.78rem;color:#cbd5e1;background:rgba(255,255,255,0.06);padding:0.2rem 0.5rem;border-radius:4px;">学習${s.studyHours}h</span>` : ''}</div>
            <div style="margin-top:0.4rem;">${subjects}</div>
          </div>
          <div style="display:flex;gap:0.4rem;flex-shrink:0;">
            <button onclick="SuccessStories._shareTwitter(${JSON.stringify(s).replace(/"/g,'&quot;')})" style="background:#000;color:white;border:none;padding:0.35rem 0.6rem;border-radius:6px;font-size:0.75rem;cursor:pointer;">𝕏</button>
            <button onclick="SuccessStories._shareLine(${JSON.stringify(s).replace(/"/g,'&quot;')})" style="background:#06c755;color:white;border:none;padding:0.35rem 0.6rem;border-radius:6px;font-size:0.75rem;cursor:pointer;">LINE</button>
          </div>
        </div>
        <div style="margin-top:0.7rem;padding:0.6rem 0.8rem;background:rgba(0,0,0,0.25);border-radius:8px;font-size:0.88rem;color:#e4e4e7;line-height:1.5;">${s.story}</div>
        ${s.advice ? `<div style="margin-top:0.5rem;padding:0.5rem 0.8rem;background:rgba(99,102,241,0.08);border-left:3px solid #6366f1;border-radius:6px;font-size:0.82rem;color:#cbd5e1;"><strong style="color:#a78bfa;">💡 後輩へのアドバイス:</strong> ${s.advice}</div>` : ''}
        ${s.seed ? `<div style="margin-top:0.5rem;font-size:0.7rem;color:#71717a;">※ サンプル体験談</div>` : ''}
      </div>`;
  }

  function renderStoriesWidget(containerId, options = {}) {
    const el = document.getElementById(containerId);
    if (!el) return;
    const stories = options.filter ? filterStories(options.filter) : getAllStories();
    const limit = options.limit || stories.length;
    if (stories.length === 0) {
      el.innerHTML = `<div style="color:#94a3b8;padding:1rem;">体験談がまだありません。</div>`;
      return;
    }
    el.innerHTML = stories.slice(0, limit).map(s => renderStoryCard(s)).join('');
  }

  function renderHomepageWidget(containerId) {
    const el = document.getElementById(containerId);
    if (!el) return;
    const stories = getAllStories().slice(0, 3);
    el.innerHTML = `
      <div style="margin-bottom:0.5rem;font-weight:800;color:#fbbf24;">🏆 合格者の声</div>
      ${stories.map(s => `
        <div style="background:rgba(255,255,255,0.04);border-left:3px solid #fbbf24;border-radius:8px;padding:0.6rem 0.85rem;margin:0.4rem 0;">
          <div style="font-weight:700;color:#fbbf24;font-size:0.9rem;">${s.school}</div>
          <div style="font-size:0.78rem;color:#a1a1aa;">${s.name} · ${s.deviationStart && s.deviationEnd ? `偏差値${s.deviationStart}→${s.deviationEnd}` : '体験談あり'}</div>
        </div>
      `).join('')}
      <div style="text-align:right;margin-top:0.4rem;"><a href="success-stories.html" style="color:#a78bfa;font-size:0.82rem;text-decoration:none;">→ 体験談をもっと見る</a></div>`;
  }

  window.SuccessStories = {
    getAllStories, addStory, deleteStory, filterStories,
    buildShareText, renderStoryCard, renderStoriesWidget, renderHomepageWidget,
    _shareLine, _shareTwitter,
  };
})();
