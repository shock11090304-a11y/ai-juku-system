export const meta = {
  name: 'kyotsu2026-recheck',
  description: '生成PDFを原本と照合: デザイン/改行の一致・誤字脱字・問題解答の整合性を4科目×3観点で検証',
  phases: [
    { title: 'Review', detail: '4科目×3観点(デザイン/誤字/整合性)=12エージェントで検証' },
    { title: 'Verify', detail: '各科目のmajor+指摘を敵対的に再確認して偽陽性を除去' },
  ],
}

const BASE = '/Users/adachishouhei/ai-juku-system/scripts/kyotsu2026_mirror'
const SPEC = `${BASE}/spec`
const CONTENT = `${BASE}/content`
const OUT = '/Users/adachishouhei/Desktop/共通テスト2026類似問題'
const ORIG = '/Users/adachishouhei/Desktop'

const SUBJECTS = [
  { key: 'math1a', name: '数学ⅠA', kind: 'math',
    orig: `${ORIG}/2026年共通テスト数学１A .pdf`,
    q: `${OUT}/数学ⅠA_問題編.pdf`, a: `${OUT}/数学ⅠA_解答編.pdf`,
    specs: 'math1a_p01-14.md, math1a_p15-28.md', parts: 'math1a_a.py(第1・2問), math1a_b.py(第3・4問)' },
  { key: 'math2bc', name: '数学ⅡBC', kind: 'math',
    orig: `${ORIG}/2026年共通テスト数学２BC.pdf`,
    q: `${OUT}/数学ⅡBC_問題編.pdf`, a: `${OUT}/数学ⅡBC_解答編.pdf`,
    specs: 'math2bc_p01-16.md, math2bc_p17-31.md, math2bc_p32-46.md',
    parts: 'math2bc_a.py(第1・2問), math2bc_b.py(第3・4問), math2bc_c.py(第5-7問)' },
  { key: 'english', name: '英語リーディング', kind: 'english',
    orig: `${ORIG}/2026年共通テスト英語.pdf`,
    q: `${OUT}/英語リーディング_問題編.pdf`, a: `${OUT}/英語リーディング_解答編.pdf`,
    specs: 'english_p01-20.md, english_p21-39.md',
    parts: 'english_a.py(第1-3問), english_b.py(第4-5問), english_c.py(第6-8問)' },
  { key: 'kokugo', name: '国語', kind: 'kokugo',
    orig: `${ORIG}/2026年共通テスト国語.pdf`,
    q: `${OUT}/国語_問題編.pdf`, a: `${OUT}/国語_解答編.pdf`,
    specs: 'kokugo_p01-17.md, kokugo_p18-34.md, kokugo_p35-51.md',
    parts: 'kokugo_a.py(第1・3問), kokugo_b.py(第2問), kokugo_c.py(第4・5問)' },
]

const FINDINGS = {
  type: 'object', additionalProperties: false,
  required: ['subject', 'dimension', 'findings', 'summary'],
  properties: {
    subject: { type: 'string' }, dimension: { type: 'string' },
    findings: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        required: ['severity', 'where', 'issue', 'fix'],
        properties: {
          severity: { enum: ['critical', 'major', 'minor'] },
          where: { type: 'string', description: 'PDF名+ページ+大問/設問など具体的位置' },
          issue: { type: 'string', description: '不具合の内容(原本との相違点/誤字/不整合)' },
          fix: { type: 'string', description: '推奨修正(どのcontentファイルのどこを直すか)' },
        },
      },
    },
    summary: { type: 'string' },
  },
}

const VERIFY = {
  type: 'object', additionalProperties: false,
  required: ['subject', 'results'],
  properties: {
    subject: { type: 'string' },
    results: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        required: ['issue', 'verdict', 'note'],
        properties: {
          issue: { type: 'string' },
          verdict: { enum: ['CONFIRMED', 'REJECTED'], description: '実際に再現するか(REJECTED=偽陽性/意図的差異)' },
          note: { type: 'string' },
        },
      },
    },
  },
}

const RENDER = `PDFはPyMuPDF(fitz)で該当ページを150dpiでPNG化してからReadで目視すること(原本はスキャン画像なので特に)。`

function designPrompt(s) {
  return `あなたは組版・デザインの厳格な照合者です。生成した共通テスト類似問題PDFが、**原本(実物2026年共通テスト)のデザイン・レイアウト・改行の作法**に忠実か照合してください。
★重要: 本文の「文言そのもの」は著作権配慮でオリジナルに差し替えてあるので、**文章内容の相違は指摘対象外**。見るのは「体裁・組版・改行密度・配置」の相違。

原本(スキャン): ${s.orig}
生成(問題編): ${s.q}
生成(解答編): ${s.a}
原本の体裁を記録した仕様書: ${SPEC}/ の ${s.specs}

${RENDER} 原本と生成を**同一箇所で並べて**比較する。照合観点:
- 大問見出しの体裁(「第N問 （配点 xx）」の書式・フォント・配置)
- 段組(1段/2段)、本文の行間・字送り・1行字数の密度感、改行位置の作法
- 選択肢の番号(①②/⓪〜)・並べ方(縦/横・段数)・字下げ
- 解答欄マーク(ア/イウ/√カ の箱、二重枠=選択式)の見た目
- 図表の配置・キャプション位置・番号(図1/表1)の付け方
- (国語)縦書き・傍線/波線・(注)・縦中横・漢文訓点の作法 / (英語)素材ボックス・語注 / (数学)会話破線枠・条件枠
- 表紙・注意事項の構成、ページ番号・柱の体裁
${s.kind === 'kokugo' ? '特に縦書きの改行・紙面分割が原本の雰囲気とずれていないか。' : ''}

原本と明確に異なる**体裁上の相違**のみを findings に(severity: 体裁が実物と大きく違う=major、細部=minor)。意図的なオリジナル差し替え(文言・数値・ブランド表紙)は指摘しない。schema で返す(dimension="design")。`
}

function typoPrompt(s) {
  return `あなたは校正者です。生成した共通テスト類似問題PDF(問題編・解答編)の**誤字・脱字・変換ミス・送り仮名の誤り・記号化け・文の途切れ・語の重複/欠落**を精査してください。

生成(問題編): ${s.q}
生成(解答編): ${s.a}
元データ(意図した文言): ${CONTENT}/ の ${s.parts}

${RENDER} 全ページを丁寧に読む。チェック:
- 誤字脱字・衍字(余分な字)・脱行、変換ミス(同音異義の誤り)、送り仮名の誤り
- 記号・数式の化け(生LaTeX/生タグ/生括弧/�/黒四角/文字重なり)
- 文が途中で切れている/意味が通らない箇所、選択肢の重複・欠落
- ${s.kind === 'english' ? '英文の綴り(spelling)・冠詞/時制・不自然な語法' : ''}${s.kind === 'kokugo' ? '古文の仮名遣い・敬語、漢文の書き下し表記、現代文の助詞の誤り' : ''}${s.kind === 'math' ? '数式・数値の表記(添字・指数・分数・単位)、問題文の日本語' : ''}
- 見出し・注・キャプションの誤記

見つけた誤りを findings に(severity: 意味に関わる=major、軽微=minor)。「正しい/問題ない」と決めつけず粗探し。schema で返す(dimension="typo")。`
}

function consistencyPrompt(s) {
  const oracle = s.kind === 'math'
    ? `数学は各スロットの正解が数学的に一意に定まる。**問題文の設定から自分で解き直し**、解答編の正解一覧・解説の値と一致するか、解説の途中式に誤りがないか検証せよ。`
    : `各設問を問題編だけ見て**自力で解答**し、解答編の正解一覧・解説と一致するか、解説の根拠が本文にあるか検証せよ。`
  return `あなたは問題と解答の整合性を検証する採点責任者です。生成した共通テスト類似問題の**問題編と解答編の食い違い**を洗い出してください。

生成(問題編): ${s.q}
生成(解答編): ${s.a}
正解データ: ${CONTENT}/ の ${s.parts} の ANS_SECTIONS

${RENDER} ${oracle}
チェック:
- 問題編の設問番号/マーク番号と、解答編の正解一覧の番号が対応しているか(ズレ・欠番・重複)
- 各設問の正解が問題として妥当で一意か(複数正解・正解なし・曖昧が無いか)
- 解答編の「正解一覧表」と「解説」の値が互いに一致するか
- 配点の合計が満点(数ⅠA/ⅡBC=100, 英語=100, 国語=200)と合うか、解説が参照するスロット名が正しいか
- 図表・条件と設問・正解の整合(例: グラフの読み取り値、順不同/完答の扱い)
- ${s.kind === 'math' ? '解説の途中式・因数分解・積分などの計算ミス' : '「適当でないものを選べ」等の設問で残り選択肢が全て妥当か'}

食い違い・誤答・曖昧を findings に(severity: 正解が誤り/非一意=critical、番号ズレ=major、解説の軽微=minor)。schema で返す(dimension="consistency")。`
}

const PROMPTS = { design: designPrompt, typo: typoPrompt, consistency: consistencyPrompt }
const DIMS = ['design', 'typo', 'consistency']

const TASKS = []
for (const s of SUBJECTS) for (const dim of DIMS) TASKS.push({ s, dim })

phase('Review')
const reviewed = await pipeline(
  TASKS,
  t => agent(PROMPTS[t.dim](t.s), { label: `${t.dim}:${t.s.key}`, phase: 'Review', schema: FINDINGS }),
  (review, t) => {
    if (!review) return null
    const bad = (review.findings || []).filter(f => f.severity !== 'minor')
    if (!bad.length) return { ...review, key: t.s.key, dim: t.dim, verified: [] }
    const list = bad.map((f, i) => `(${i + 1})[${f.severity}] ${f.where} — ${f.issue}`).join('\n')
    const vp = `以下は「${t.s.name}」の${t.dim}レビューで挙がった major/critical 指摘です。各指摘を実際にPDFで再確認し、本当に不具合か(=CONFIRMED)、偽陽性または意図的なオリジナル差し替え/仕様準拠か(=REJECTED)を判定してください。
生成(問題編): ${t.s.q}
生成(解答編): ${t.s.a}
原本: ${t.s.orig}
${RENDER}
指摘一覧:
${list}
各指摘に verdict を付けて schema で返す(subject="${t.s.key}:${t.dim}")。`
    return agent(vp, { label: `verify:${t.dim}:${t.s.key}`, phase: 'Verify', schema: VERIFY })
      .then(v => ({ ...review, key: t.s.key, dim: t.dim, verified: (v && v.results) || [] }))
  }
)

const clean = reviewed.filter(Boolean)
// CONFIRMED として残った major/critical と、全 minor をまとめて返す
const confirmed = []
for (const r of clean) {
  const conf = new Set((r.verified || []).filter(v => v.verdict === 'CONFIRMED').map(v => v.issue))
  for (const f of (r.findings || [])) {
    const isMinor = f.severity === 'minor'
    const survived = isMinor || [...conf].some(c => c.includes(f.issue.slice(0, 12)) || f.issue.includes(c.slice(0, 12)))
    if (survived) confirmed.push({ subject: r.key, dimension: r.dim, ...f })
  }
}
return {
  total_findings: clean.reduce((n, r) => n + (r.findings || []).length, 0),
  confirmed_or_minor: confirmed,
  per_subject: clean.map(r => ({ subject: r.key, dim: r.dim, n: (r.findings || []).length, summary: r.summary })),
}
