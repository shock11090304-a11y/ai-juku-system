export const meta = {
  name: 'math-v2-final-qa',
  description: '第2集(図形強化)の最終QA: 全64頁を目視(図の正しさ重視)+全209問を独立再導出、各指摘を敵対的に確認',
  phases: [
    { title: 'PageProof', detail: '全ページ画像を目視(図の正誤/描画/レイアウト/記号)' },
    { title: 'AnswerAudit', detail: '分野ごとに全問の答えを独立再導出' },
    { title: 'Verify', detail: '各指摘を敵対的に確認' },
  ],
}

const QD = '/private/tmp/claude-501/-Users-adachishouhei-ai-juku-system/ebb3897a-3aef-4574-b334-0fe7a6e8a298/scratchpad/qa2'
const DIR = '/Users/adachishouhei/ai-juku-system/scripts/math_workbook'
const IA_PAGES = 31, IIB_PAGES = 33

const FIND_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['findings'],
  properties: { findings: { type: 'array', items: {
    type: 'object', additionalProperties: false,
    required: ['location', 'category', 'severity', 'detail', 'fix'],
    properties: {
      location: { type: 'string' },
      category: { type: 'string', enum: ['figure', 'render', 'layout', 'notation', 'answer', 'wording', 'other'] },
      severity: { type: 'string', enum: ['high', 'medium', 'low'] },
      detail: { type: 'string' }, fix: { type: 'string' },
    } } } },
}
const VERDICT_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['verdict', 'note'],
  properties: { verdict: { type: 'string', enum: ['confirmed', 'refuted', 'uncertain'] }, note: { type: 'string' } },
}

function pageList(book, n) {
  const a = []
  for (let i = 0; i < n; i++) a.push(`${QD}/${book}_p${String(i).padStart(2, '0')}.png`)
  return a
}
const allPages = [...pageList('ia2', IA_PAGES), ...pageList('iib2', IIB_PAGES)]
const BATCH = 6
const batches = []
for (let i = 0; i < allPages.length; i += BATCH) batches.push(allPages.slice(i, i + BATCH))

log(`第2集QA: ページ目視 ${batches.length}バッチ + 答え再導出 19分野`)

const proofPromises = batches.map((paths, bi) => () => agent(
  `あなたは図形入り数学教材の校閲者です。次のPDFページ画像を1枚ずつ Read して目視し、問題を報告してください。\n` +
  paths.map(p => `- ${p}`).join('\n') +
  `\n\n特に【図(SVG)の正しさ】を重点的に:\n` +
  `- figure: 図が問題文と整合しているか(与えられた辺の長さ・角・点・ベクトルの向き・座標が図と一致)。三角形/円/座標/立体の位置関係が正しいか。直角マーク・ラベル(A,B,C,O等)が正しい位置か。★図に答え(未知数の値)が描かれて答えがバレていないか。図が乱れて読めない/はみ出していないか。\n` +
  `そのほか:\n` +
  `- render: 数式の崩れ・KaTeX赤エラー・$の生残り・文字化け。notation: 日本語が数式(斜体)になっていないか、教科書記号(ベクトル上矢印/組分数/√被覆/∫Σ)が正しいか。\n` +
  `- layout: 問題のページ跨ぎ割れ・右端切れ・図と本文の重なり・見出し重複・過度な空白。柱とノンブルの有無。\n` +
  `見つけた問題だけ findings に(location はファイル名と問番号)。無ければ空配列。実際に画像を見た事実のみ。`,
  { label: `proof:b${bi}`, phase: 'PageProof', schema: FIND_SCHEMA, effort: 'high' }
))

const UNIT_TASKS = []
for (const [book, n] of [['ia2', 9], ['iib2', 10]]) for (let ui = 0; ui < n; ui++) UNIT_TASKS.push({ book, ui })
const auditPromises = UNIT_TASKS.map((t) => () => agent(
  `あなたは数学の採点者です。JSONファイル ${DIR}/qa_${t.book}.json を Read し、その ${t.ui} 番目(0始まり)の分野の各問題を、問題文(stem)だけ読んで自分で一から解き(必要なら sympy を Bash で)、テキストの answer と一致するか照合してください。\n` +
  `報告: 1.answer=表示された答えが数学的に誤り。2.wording=一意に解けない/範囲不整合/選択肢と正解ズレ。3.answerのLaTeXが値として矛盾(分子分母取り違え等)。\n` +
  `間違いのみ findings に(location「${t.book}/分野名#問番号」, category は answer か wording)。全問正しければ空配列。自力計算に基づくこと。`,
  { label: `audit:${t.book}:u${t.ui}`, phase: 'AnswerAudit', schema: FIND_SCHEMA, effort: 'high' }
))

const [proofResults, auditResults] = await Promise.all([parallel(proofPromises), parallel(auditPromises)])
const all = []
for (const r of [...proofResults, ...auditResults]) if (r && Array.isArray(r.findings)) all.push(...r.findings)
log(`一次指摘 ${all.length}件 → 敵対的確認`)
if (all.length === 0) return { confirmed: [], raw_count: 0 }

const verified = await parallel(all.map((f) => () =>
  agent(
    `次の「指摘」が本当に修正を要する実在の問題か敵対的に検証。既定は refuted を疑い、確かな根拠があるときだけ confirmed。\n` +
    `画像 ${QD}/ 配下、元データ ${DIR}/qa_ia2.json / qa_iib2.json / content_ia_v2.py / content_iib_v2.py を必要に応じ Read/計算して確かめる。\n\n指摘: ${JSON.stringify(f)}\n\n` +
    `図の誤り/描画崩れ/レイアウト破綻/答えの誤り が実在するか判定し verdict を返す。`,
    { label: `vfy:${(f.location || '').slice(0, 22)}`, phase: 'Verify', schema: VERDICT_SCHEMA, effort: 'high' }
  ).then(v => ({ finding: f, ...v }))
))
const confirmed = verified.filter(Boolean).filter(v => v.verdict === 'confirmed').map(v => ({ ...v.finding, note: v.note }))
const uncertain = verified.filter(Boolean).filter(v => v.verdict === 'uncertain').map(v => ({ ...v.finding, note: v.note }))
return { confirmed, uncertain, raw_count: all.length }
