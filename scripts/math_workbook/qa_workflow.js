export const meta = {
  name: 'math-final-qa',
  description: '数IA/IIB 完成PDFの最終QA: 全48頁の描画/レイアウト/記号を目視監査 + 全問の答えを独立再導出、各指摘を敵対的に確認',
  phases: [
    { title: 'PageProof', detail: '全ページ画像を目視(描画崩れ/日本語のmath混入/レイアウト/記号)' },
    { title: 'AnswerAudit', detail: '分野ごとに全問の答えを独立再導出' },
    { title: 'Verify', detail: '各指摘を敵対的に確認' },
  ],
}

const QD = '/private/tmp/claude-501/-Users-adachishouhei-ai-juku-system/ebb3897a-3aef-4574-b334-0fe7a6e8a298/scratchpad/qa'
const DIR = '/Users/adachishouhei/ai-juku-system/scripts/math_workbook'
const IA_PAGES = 25, IIB_PAGES = 23

const FIND_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['findings'],
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        required: ['location', 'category', 'severity', 'detail', 'fix'],
        properties: {
          location: { type: 'string' },
          category: { type: 'string', enum: ['render', 'layout', 'notation', 'answer', 'wording', 'other'] },
          severity: { type: 'string', enum: ['high', 'medium', 'low'] },
          detail: { type: 'string' },
          fix: { type: 'string' },
        },
      },
    },
  },
}

const VERDICT_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['verdict', 'note'],
  properties: {
    verdict: { type: 'string', enum: ['confirmed', 'refuted', 'uncertain'] },
    note: { type: 'string' },
  },
}

// ---- ページ画像バッチ ----
function pageList(book, n) {
  const a = []
  for (let i = 0; i < n; i++) a.push(`${QD}/${book}_p${String(i).padStart(2, '0')}.png`)
  return a
}
const allPages = [...pageList('ia', IA_PAGES), ...pageList('iib', IIB_PAGES)]
const BATCH = 6
const batches = []
for (let i = 0; i < allPages.length; i += BATCH) batches.push(allPages.slice(i, i + BATCH))

log(`最終QA: ページ目視 ${batches.length}バッチ + 答え再導出 18分野`)

const proofPromises = batches.map((paths, bi) => () => agent(
  `あなたは印刷教材の校閲者です。次の高校数学PDFのページ画像を1枚ずつ Read して目視し、問題を報告してください。\n` +
  paths.map(p => `- ${p}`).join('\n') +
  `\n\n各ページで次を厳しくチェック:\n` +
  `1. render: 数式が崩れていないか。KaTeXの赤いエラー表示、$記号の生残り、文字化け(豆腐)、記号の欠け。\n` +
  `2. notation混入: 日本語の地の文が数式(斜体の英字/変な字間)として描画されていないか(=日本語が$の中に入ってしまった兆候)。ベクトルは文字の「上」に矢印か。分数は上下に積んだ組分数か。√は被覆線付きか。∫Σは上下限が正しいか。補集合は上線か。\n` +
  `3. layout: 問題が途中でページ跨ぎに割れていないか、右端で文字が切れていないか、行重なり、空白過多。\n` +
  `4. 体裁: 柱(ヘッダ書名)とノンブル(ページ番号)が出ているか。分野帯・難易度ラベルの色。\n` +
  `見つけた問題だけを findings に(location はファイル名と問番号)。問題が無ければ findings は空配列。憶測せず、実際に画像を見た事実だけ報告。`,
  { label: `proof:batch${bi}`, phase: 'PageProof', schema: FIND_SCHEMA, effort: 'high' }
))

const UNIT_TASKS = []
for (const [book, n] of [['ia', 9], ['iib', 9]]) {
  for (let ui = 0; ui < n; ui++) UNIT_TASKS.push({ book, ui })
}
const auditPromises = UNIT_TASKS.map((t) => () => agent(
  `あなたは数学の採点者です。JSONファイル ${DIR}/qa_${t.book}.json を Read し、その ${t.ui} 番目(0始まり)の分野の各問題について、**問題文(stem)だけを読んで自分で一から解き**、テキストに載っている answer と一致するか照合してください(必要なら sympy を Bash で使ってよい)。\n` +
  `LaTeX表記($...$, \\dfrac, \\vec, \\sqrt 等)で書かれている。次を報告:\n` +
  `1. answer: 表示された答えが数学的に間違っている問題(category=answer)。\n` +
  `2. wording: 問題文が曖昧/条件不足で一意に解けない、範囲指定(例 0≦θ<2π)と答えが不整合、選択肢と正解のズレ。\n` +
  `3. 表示された answer の LaTeX が、値として問題と矛盾していないか(例: 分子分母の取り違え)。\n` +
  `間違いのみ findings に(location は「${t.book}/分野名#問番号」)。全問正しければ空配列。必ず自分で計算した結果に基づくこと。`,
  { label: `audit:${t.book}:u${t.ui}`, phase: 'AnswerAudit', schema: FIND_SCHEMA, effort: 'high' }
))

const [proofResults, auditResults] = await Promise.all([
  parallel(proofPromises),
  parallel(auditPromises),
])

const all = []
for (const r of [...proofResults, ...auditResults]) {
  if (r && Array.isArray(r.findings)) all.push(...r.findings)
}
log(`一次指摘 ${all.length}件 → 敵対的確認へ`)

if (all.length === 0) {
  return { confirmed: [], raw_count: 0, note: '指摘ゼロ' }
}

const verified = await parallel(all.map((f) => () =>
  agent(
    `次の「指摘」が本当に修正を要する実在の問題か、敵対的に検証してください。既定では refuted(=問題なし)を疑い、確かな根拠がある場合のみ confirmed にする。\n` +
    `対象PDFのページ画像や元データ(${DIR}/qa_ia.json, qa_iib.json, ${DIR}/content_ia.py, content_iib.py)や画像(${QD}/ 配下)を必要に応じて Read/計算して確かめること。\n\n` +
    `指摘: ${JSON.stringify(f)}\n\n` +
    `本当に描画崩れ/日本語混入/レイアウト破綻/答えの誤り が「その場所に実在する」か確認し、verdict を返す。`,
    { label: `verify:${(f.location || '').slice(0, 24)}`, phase: 'Verify', schema: VERDICT_SCHEMA, effort: 'high' }
  ).then(v => ({ finding: f, ...v }))
))

const confirmed = verified.filter(Boolean).filter(v => v.verdict === 'confirmed').map(v => ({ ...v.finding, note: v.note }))
const uncertain = verified.filter(Boolean).filter(v => v.verdict === 'uncertain').map(v => ({ ...v.finding, note: v.note }))
return { confirmed, uncertain, raw_count: all.length }
