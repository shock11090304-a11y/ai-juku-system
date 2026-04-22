// AI Content Studio - Generate SEO-optimized articles
const API_URL = 'https://api.anthropic.com/v1/messages';
const MODEL = 'claude-sonnet-4-6';

let lastMarkdown = '';
let lastHtml = '';
let lastJson = null;

function getApiKey() {
  return localStorage.getItem('ai_juku_api_key');
}

function updateMode() {
  const hasKey = !!getApiKey();
  const indicator = document.getElementById('modeIndicator');
  if (hasKey) {
    indicator.textContent = '🟢 Live (Claude API)';
    indicator.className = 'mode-badge live';
  } else {
    indicator.textContent = '🟡 デモモード';
    indicator.className = 'mode-badge demo';
  }
}

async function generateArticle() {
  const topic = document.getElementById('articleTopic').value.trim();
  const category = document.getElementById('articleCategory').value;
  const keywords = document.getElementById('articleKeywords').value.trim();
  const target = document.getElementById('articleTarget').value;
  const length = document.getElementById('articleLength').value;
  const tone = document.getElementById('articleTone').value;
  const notes = document.getElementById('articleNotes').value.trim();

  if (!topic) { alert('テーマ・タイトル案を入力してください'); return; }

  const preview = document.getElementById('articlePreview');
  const actions = document.getElementById('outputActions');
  const tabs = document.getElementById('outputTabs');
  const btn = document.getElementById('generateArticleBtn');

  btn.disabled = true;
  btn.textContent = '⏳ 生成中...';
  preview.innerHTML = '<p class="placeholder">✨ AIが記事を執筆中... (20-60秒)</p>';
  actions.style.display = 'none';
  tabs.style.display = 'none';

  const systemPrompt = `あなたはSEOに精通した教育系メディアの編集者です。AI学習塾「AI学習コーチ塾」のブログ記事を、検索エンジンからの流入を最大化する形で執筆してください。

【厳守事項】
- タイトル（h1）は32-40文字、クリック率の高い形式（問いかけ・数字・ベネフィット）
- 見出し（h2）は5-7個、各見出しの下に2-3段落
- ターゲットキーワードを自然に配置（不自然な詰め込みNG）
- 読者の悩みに共感→解決策→具体例→CTAの構造
- 最後に必ず「AI学習コーチ塾」への自然なCTA
- ${length}字程度

【出力形式】
必ず以下のJSON形式で、他のテキストは含めず純粋なJSONのみ返してください:
{
  "slug": "url-friendly-slug",
  "title": "記事タイトル",
  "description": "meta description (120-140字)",
  "category": "${category}",
  "tags": ["タグ1", "タグ2", "タグ3", "タグ4", "タグ5"],
  "excerpt": "記事の引きつけるリード文 (80-100字)",
  "coverEmoji": "記事内容を表す絵文字1つ",
  "readMinutes": 推定読了分数,
  "content": "HTMLフォーマットの記事本文。<h2>, <h3>, <p>, <ul>, <ol>, <li>, <strong>, <em>, <blockquote>を使用可。コードブロックなどは使わない"
}`;

  const userMsg = `テーマ: ${topic}
カテゴリ: ${category}
ターゲット読者: ${target}
メインキーワード: ${keywords}
文字数: ${length}字
トーン: ${tone}
${notes ? `\n追加要件:\n${notes}` : ''}

上記の条件で、SEO最適化されたブログ記事を指定のJSON形式で生成してください。`;

  const apiKey = getApiKey();
  let result;

  if (!apiKey) {
    // Demo response
    await new Promise(r => setTimeout(r, 1500));
    result = generateDemoArticle(topic, category, keywords, target);
  } else {
    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': apiKey,
          'anthropic-version': '2023-06-01',
          'anthropic-dangerous-direct-browser-access': 'true'
        },
        body: JSON.stringify({
          model: MODEL,
          max_tokens: 4000,
          system: systemPrompt,
          messages: [{ role: 'user', content: userMsg }],
        }),
      });
      if (!res.ok) throw new Error(`API error ${res.status}`);
      const data = await res.json();
      const text = data.content?.[0]?.text || '{}';
      result = JSON.parse(text.replace(/^```json\s*|\s*```$/g, ''));
    } catch (e) {
      preview.innerHTML = `<p style="color:var(--error);padding:2rem;">⚠️ エラー: ${e.message}<br><br>デモ応答を表示します。</p>`;
      result = generateDemoArticle(topic, category, keywords, target);
    }
  }

  lastJson = result;
  lastMarkdown = buildMarkdown(result);
  lastHtml = result.content;

  renderPreview(result);
  actions.style.display = 'flex';
  tabs.style.display = 'flex';
  btn.disabled = false;
  btn.textContent = '✨ 記事を生成';
}

function generateDemoArticle(topic, category, keywords, target) {
  const slug = topic.slice(0, 30).replace(/[^\w\s-]/g, '').replace(/\s+/g, '-').toLowerCase() || 'new-article';
  return {
    slug,
    title: topic + '：実践的な活用ガイド',
    description: `${target}向けに、${topic}について徹底解説。具体的な方法、注意点、成功事例を紹介します。AI学習コーチ塾の教育専門家が監修。`,
    category,
    tags: (keywords || '学習,AI,教育').split(/[,、\s]+/).filter(Boolean).slice(0, 5),
    excerpt: `${topic}についてお悩みの${target}の方へ。この記事を読めば、明日から実践できる具体的な方法がわかります。`,
    coverEmoji: '📚',
    readMinutes: 5,
    content: `
<h2>はじめに：なぜ今、${topic}が注目されているのか</h2>
<p>2026年、教育の世界は大きく変化しています。特に「${topic}」というテーマは、${target}にとって見逃せない重要トピックとなっています。本記事では、実践的な視点から、${topic}の本質と活用法を解説します。</p>
<p>AIの急速な進化により、学習の方法論は根本的に変わりつつあります。かつては高額な個別指導でしか得られなかった個別最適化が、今や月額2万円台で実現できる時代となりました。</p>

<h2>1. ${topic}の基本的な考え方</h2>
<p>まず押さえておきたいのは、<strong>${topic}は一朝一夕に身につくものではない</strong>ということです。継続と正しい方向性が重要です。特に以下の3点を意識してください：</p>
<ul>
  <li>毎日少しずつでも取り組む継続性</li>
  <li>定期的な振り返りと軌道修正</li>
  <li>専門家の伴走サポート</li>
</ul>

<h2>2. 実践の第一歩：具体的な方法</h2>
<p>${topic}を実践する際、多くの${target}が最初に躓くのが「何から始めればいいかわからない」という点です。以下のステップで進めることをおすすめします：</p>
<h3>ステップ1：現状把握</h3>
<p>まずは現在の状況を客観的に把握しましょう。模試の成績、日々の学習時間、苦手分野などを書き出してみてください。</p>
<h3>ステップ2：目標設定</h3>
<p>3ヶ月後、6ヶ月後、1年後の目標を具体的に設定します。「偏差値を5上げる」「英検2級に合格する」など、測定可能な目標にすることが重要です。</p>
<h3>ステップ3：計画立案と実行</h3>
<p>目標達成のための学習計画を立てます。ここでAIチューターが威力を発揮します。</p>

<h2>3. よくある失敗とその対策</h2>
<p>${topic}に取り組む上で、多くの人が陥る失敗パターンがあります：</p>
<blockquote>「最初の1週間だけ頑張って、その後続かない」──これは典型的な失敗パターンです。解決策は、<strong>毎日の学習量を最初から多くしすぎないこと</strong>です。</blockquote>
<p>持続可能なペースを最初に見極めることが、長期的な成功の鍵となります。</p>

<h2>4. AIを活用した新しいアプローチ</h2>
<p>従来の方法に加えて、AIチューターを活用することで、学習効率は劇的に向上します。特に以下の点で効果を発揮します：</p>
<ul>
  <li>24時間いつでも質問できる環境</li>
  <li>個別最適化されたカリキュラム</li>
  <li>無制限の問題演習と添削</li>
</ul>

<h2>5. 成功事例：実際に成果を出した${target}の声</h2>
<p>実際にAI学習コーチ塾を活用して成果を出した方々の声をご紹介します：</p>
<blockquote>「毎日の学習習慣が定着し、偏差値が半年で8上がりました。AIチューターに深夜でも質問できるのが本当に助かります」──実績者談</blockquote>

<h2>まとめ：今日から始める3つのアクション</h2>
<p>最後に、今日から実践できる具体的なアクションをまとめます：</p>
<ol>
  <li><strong>現状分析シートを作成する</strong>：15分で完了</li>
  <li><strong>3ヶ月後の目標を書き出す</strong>：10分で完了</li>
  <li><strong>AI学習塾の無料体験に申し込む</strong>：5分で完了</li>
</ol>
<p>AI学習コーチ塾では、<strong>3日間の無料体験</strong>を実施中です。クレジットカード登録不要で、気軽にお試しいただけます。${topic}でお悩みの${target}の方、ぜひこの機会にお試しください。</p>
<p><em>💡 デモ応答：APIキーを設定すると、実際のAIが各条件に応じた本格的な記事を生成します。</em></p>
    `,
  };
}

function buildMarkdown(article) {
  const html = article.content;
  const md = html
    .replace(/<h2>(.*?)<\/h2>/g, '## $1')
    .replace(/<h3>(.*?)<\/h3>/g, '### $1')
    .replace(/<p>(.*?)<\/p>/g, '$1\n')
    .replace(/<ul>([\s\S]*?)<\/ul>/g, (_, content) =>
      content.replace(/<li>(.*?)<\/li>/g, '- $1').trim())
    .replace(/<ol>([\s\S]*?)<\/ol>/g, (_, content) => {
      let i = 1;
      return content.replace(/<li>(.*?)<\/li>/g, () => `${i++}. $1`).trim();
    })
    .replace(/<strong>(.*?)<\/strong>/g, '**$1**')
    .replace(/<em>(.*?)<\/em>/g, '*$1*')
    .replace(/<blockquote>(.*?)<\/blockquote>/gs, '> $1')
    .replace(/<[^>]+>/g, '')
    .replace(/\n{3,}/g, '\n\n')
    .trim();

  return `# ${article.title}\n\n**${article.description}**\n\n---\n\n${md}`;
}

function renderPreview(article) {
  const preview = document.getElementById('articlePreview');
  renderView('rendered');
}

function renderView(view) {
  const preview = document.getElementById('articlePreview');
  if (!lastJson) return;

  if (view === 'rendered') {
    preview.innerHTML = `<h1>${escapeHtml(lastJson.title)}</h1>
<p style="color:var(--text-dim);font-style:italic;margin-bottom:1.5rem;">${escapeHtml(lastJson.description)}</p>
${lastJson.content}`;
  } else if (view === 'markdown') {
    preview.innerHTML = `<pre>${escapeHtml(lastMarkdown)}</pre>`;
  } else if (view === 'json') {
    preview.innerHTML = `<pre>${escapeHtml(JSON.stringify(lastJson, null, 2))}</pre>`;
  }
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c]));
}

// Event handlers
document.addEventListener('DOMContentLoaded', () => {
  updateMode();

  document.getElementById('generateArticleBtn').addEventListener('click', generateArticle);

  document.getElementById('copyMdBtn').addEventListener('click', () => {
    navigator.clipboard.writeText(lastMarkdown).then(() => alert('✅ Markdownをコピーしました'));
  });
  document.getElementById('copyHtmlBtn').addEventListener('click', () => {
    navigator.clipboard.writeText(lastHtml).then(() => alert('✅ HTMLをコピーしました'));
  });
  document.getElementById('saveJsonBtn').addEventListener('click', () => {
    const jsonStr = JSON.stringify({
      slug: lastJson.slug,
      title: lastJson.title,
      description: lastJson.description,
      category: lastJson.category,
      tags: lastJson.tags,
      author: 'AI学習コーチ塾 編集部',
      date: new Date().toISOString().slice(0, 10),
      readMinutes: lastJson.readMinutes,
      coverEmoji: lastJson.coverEmoji,
      excerpt: lastJson.excerpt,
      content: lastJson.content,
    }, null, 2);
    navigator.clipboard.writeText(jsonStr).then(() =>
      alert('✅ articles.js用のJSONをコピーしました\n\narticles.jsのARRAYに貼り付けてください。')
    );
  });

  document.querySelectorAll('.output-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.output-tab').forEach(t => t.classList.toggle('active', t === tab));
      renderView(tab.dataset.view);
    });
  });

  document.querySelectorAll('.idea-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      document.getElementById('articleTopic').value = chip.dataset.title;
      document.getElementById('articleTopic').scrollIntoView({ behavior: 'smooth' });
    });
  });
});
