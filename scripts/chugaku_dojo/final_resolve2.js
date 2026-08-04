export const meta = {
  name: 'chugaku-final-resolve2',
  description: 'part別 投入後の最終盲再解答: DB保存済(add2/_stored_blind_<part>.json, 正解伏せ)を単元ごと2独立ソルバー(事実科目は1名WebSearch)が解き、保存キー照合用に返す。',
  phases: [{ title: 'ReSolve', detail: '保存済データを盲で再解答' }],
}

const A = typeof args === 'string' ? JSON.parse(args) : args
const PART = A.part, SUBJECT = A.subject
const UNITS = A.units   // [{filter, factcheck}]
const BLIND = `scripts/chugaku_dojo/add2/_stored_blind_${PART}.json`

const SCHEMA = { type: 'object', additionalProperties: false, required: ['answers'], properties: { answers: { type: 'array', items: { type: 'object', additionalProperties: false, required: ['gid', 'choice_index', 'confident'], properties: { gid: { type: 'string' }, choice_index: { type: 'integer', minimum: 0, maximum: 3 }, confident: { type: 'boolean' } } } } } }

function prompt(u, lens) {
  const lensText = lens === 'fact'
    ? '年号・人名・制度・地名・数値・語義・法則など事実は、少しでも不確かなら WebSearch(必要なら ToolSearch で有効化)で裏取りして、事実として正しい選択肢を選ぶ。'
    : '自力で最後まで解いてから答えを選ぶ。'
  return `ファイル ${BLIND} を Read ツールで読んでください(JSON配列 {gid, unit, passage, stem, choices})。unit === "${u.filter}" の設問だけを対象に、正解を伏せた状態で独立に解答します(passage があればそれも読む)。
${lensText}
各設問について最も正しい選択肢の0始まりindexを1つ選び answers[{gid, choice_index, confident}] を返す。confident=一意に確信できるか。出力は指定スキーマJSONのみ。`
}

const out = await parallel(UNITS.map((u) => async () => {
  const lensB = u.factcheck ? 'fact' : 'reason'
  const [a, b] = await parallel([
    () => agent(prompt(u, 'reason'), { label: `re:${PART}/${u.filter}`, phase: 'ReSolve', schema: SCHEMA, agentType: 'general-purpose' }),
    () => agent(prompt(u, lensB), { label: `${lensB}:${PART}/${u.filter}`, phase: 'ReSolve', schema: SCHEMA, agentType: 'general-purpose', effort: 'high' }),
  ])
  const m = (r) => (r && Array.isArray(r.answers)) ? r.answers : []
  return { filter: u.filter, solverA: m(a), solverB: m(b) }
}))

return { part: PART, units: out.filter(Boolean) }
