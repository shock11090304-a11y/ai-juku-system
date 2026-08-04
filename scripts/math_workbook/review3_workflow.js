export const meta = {
  name: 'math-v2-figure-instruction-review',
  description: '第2集の全図を問題文と厳密照合(ラベル/長さ/角/座標/ベクトル向き/領域/幾何妥当性)＋指示の整合(図中要素/下線/斜線/空欄/グラフ)を独立検証、各指摘を敵対的に確認',
  phases: [
    { title: 'FigureProof', detail: '全ページの図を問題文と照合＋指示整合を検証' },
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
      category: { type: 'string', enum: ['figure-mismatch', 'figure-geometry', 'figure-labels', 'answer-leak', 'instruction', 'render', 'other'] },
      severity: { type: 'string', enum: ['high', 'medium', 'low'] },
      detail: { type: 'string' }, fix: { type: 'string' },
    } } } },
}
const VERDICT_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['verdict', 'note'],
  properties: { verdict: { type: 'string', enum: ['confirmed', 'refuted', 'uncertain'] }, note: { type: 'string' } },
}

function pageList(book, n) { const a=[]; for (let i=0;i<n;i++) a.push(`${QD}/${book}_p${String(i).padStart(2,'0')}.png`); return a }
const allPages = [...pageList('ia2', IA_PAGES), ...pageList('iib2', IIB_PAGES)]
const BATCH = 5
const batches = []
for (let i=0;i<allPages.length;i+=BATCH) batches.push(allPages.slice(i,i+BATCH))
log(`図・指示レビュー: ${batches.length}バッチ`)

const proofPromises = batches.map((paths, bi) => () => agent(
  `あなたは数学教材の図版校閲の専門家です。次のPDFページ画像を1枚ずつ Read し、各問題について【図と問題文の厳密な対応】と【指示の実行可能性】を検証してください。参考に元データ ${DIR}/qa_ia2.json / qa_iib2.json も Read してよい(stem/answer/has_figure)。\n` +
  paths.map(p => `- ${p}`).join('\n') +
  `\n\n【A. 図の正しさ(figureのある問題すべて)】1問ずつ厳密に:\n` +
  `1. figure-labels: 図に書かれた辺の長さ・角度・座標・頂点名(A,B,C,O,P)・ベクトル名が、問題文で与えられた値と完全に一致するか(例: 文でAB=3なのに図で4、角が文と違う、点の座標が逆)。\n` +
  `2. figure-mismatch/geometry: 図の位置関係が正しいか。座標問題は点が正しい象限/軸の上下(SVGなので y負は軸の下)にあるか、直線の傾きの正負・向きが式と合うか、円が正しい位置・中心・半径か、内接円は3辺に接するか、ベクトルの矢印の向きが成分と合うか、直角マーク・平行/等辺マークが正しいか。三角形や立体の形が問題と矛盾しないか。\n` +
  `3. answer-leak: 図に答え(未知数の値・求める長さや角)が書かれてしまっていないか。\n` +
  `【B. 指示の整合(全問)】:\n` +
  `4. instruction: 問題文が「図のように点Pを」「図の角θ」「斜線部の面積」「下線部」「空欄アに入る」等と参照しているのに、図・本文にその要素(点P/角θ/塗り領域/下線/空欄)が無い、という不整合が無いか。「〜を求めよ/示せ/選べ」の指示が、示された情報だけで一意に実行できるか。選択肢問題は選択肢が過不足ないか。\n` +
  `5. render: 数式の崩れ・\\nなどの生エスケープ露出・文字化け・図のはみ出し/重なり。\n\n` +
  `問題があるものだけ findings に(location=ファイル名と問番号、category を選ぶ)。無ければ空配列。必ず実際に画像を見て、問題文と1つずつ突き合わせた事実のみ。憶測禁止。`,
  { label: `figproof:b${bi}`, phase: 'FigureProof', schema: FIND_SCHEMA, effort: 'high' }
))

const results = await parallel(proofPromises)
const all = []
for (const r of results) if (r && Array.isArray(r.findings)) all.push(...r.findings)
log(`一次指摘 ${all.length}件 → 敵対的確認`)
if (all.length === 0) return { confirmed: [], raw_count: 0 }

const verified = await parallel(all.map((f) => () =>
  agent(
    `次の「図/指示に関する指摘」が本当に修正を要する実在の問題か、敵対的に検証してください。既定では refuted を疑い、画像(${QD}/配下)と元データ(${DIR}/qa_ia2.json / qa_iib2.json / content_ia_v2.py / content_iib_v2.py)を Read・計算して確かめ、確かな根拠があるときだけ confirmed。図のラベルと問題文の値の不一致、幾何の誤り、答え露出、指示と図中要素の不整合が「その場所に実在する」かを判定。\n\n指摘: ${JSON.stringify(f)}`,
    { label: `vfy:${(f.location||'').slice(0,22)}`, phase: 'Verify', schema: VERDICT_SCHEMA, effort: 'high' }
  ).then(v => ({ finding: f, ...v }))
))
const confirmed = verified.filter(Boolean).filter(v => v.verdict === 'confirmed').map(v => ({ loc: v.finding.location, cat: v.finding.category, sev: v.finding.severity, fix: (v.finding.fix || '').slice(0, 160) }))
const uncertain = verified.filter(Boolean).filter(v => v.verdict === 'uncertain').map(v => ({ loc: v.finding.location, sev: v.finding.severity }))
return { confirmed, uncertain, raw_count: all.length }
