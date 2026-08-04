export const meta = {
  name: 'chugaku-topup-expand',
  description: 'DROPで不足した中学ドリル単元(英/国/理/社)を追加生成。既存DB stem+追加済 add2 stem を避けて作問→3独立盲ソルバー(事実科目はWebSearch)全員一致→不足数だけ採用。',
  phases: [{ title: 'Author', detail: '不足単元を全stem回避で作問' }, { title: 'Verify', detail: '3独立盲ソルバー全員一致' }],
}

const A = typeof args === 'string' ? JSON.parse(args) : args
const PART = A.part, SUBJECT = A.subject
const UNITS = (A.units || []).map((u) => ({ ...u, gen: Math.max(6, Math.ceil(u.need * 2)) }))

const SUBJ_HINT = {
  '英語': '公立高校入試 標準の文法・語法・適語補充・語形変化・対話応答。ネイティブが認める正解が1つに定まる問題のみ。図・本文なしで解ける自己完結。',
  '国語': '中学国語の知識問題(漢字/語句慣用句四字熟語/文法品詞活用/敬語/古文の基礎/詩歌の知識)。本文不要の自己完結。教科書レベルの定説のみ。',
  '理科': '中学理科の教科書事実のみ。用語・法則・数値・単位・実験結果を正確に。図必須は避け条件は文章で。高校範囲/諸説は不可。',
  '社会': '中学社会の教科書事実のみ(公立入試頻出)。年号・人名・制度・地名・因果・統計を正確に。諸説/細かすぎ/時事変動は避ける。',
}

const AUTHOR_SCHEMA = { type: 'object', additionalProperties: false, required: ['questions'], properties: { questions: { type: 'array', items: { type: 'object', additionalProperties: false, required: ['stem', 'choices', 'answer_index', 'unit', 'explanation'], properties: { stem: { type: 'string' }, choices: { type: 'array', items: { type: 'string' }, minItems: 4, maxItems: 4 }, answer_index: { type: 'integer', minimum: 0, maximum: 3 }, unit: { type: 'string' }, explanation: { type: 'string' } } } } } }
const SOLVE_SCHEMA = { type: 'object', additionalProperties: false, required: ['answers'], properties: { answers: { type: 'array', items: { type: 'object', additionalProperties: false, required: ['i', 'choice_index', 'confident'], properties: { i: { type: 'integer' }, choice_index: { type: 'integer', minimum: 0, maximum: 3 }, confident: { type: 'boolean' } } } } } }

function authorPrompt(u) {
  return `あなたは公立高校入試 標準の「${SUBJECT}」作問のプロです。単元「${u.filter}」の4択問題を ${u.gen} 問つくってください。
【重複回避】Read ツールで次を読み既出と重複しない新問だけ作る: scripts/chugaku_dojo/add2/_stems_${PART}.json のキー「${u.filter}」、および scripts/chugaku_dojo/add2/${PART}__${u.gi}.json(存在すれば各 stem)。
【要点】${SUBJ_HINT[SUBJECT] || ''}
【厳守】1.4択・正解1つ・一意(2正解/曖昧禁止)。2.answer_index=0始index、choices4つ相異なり正解と同値の選択肢を入れない。3.unit は "${u.filter}"。4.図/本文なしで解ける自己完結・事実/語形/数値は厳密。5.explanation は 【単元】${u.filter}。正解は「<正解text>」。 で始め値・理由のみ(位置表記ア/A/①/N番目 禁止)。${u.factcheck ? '6.年号/人名/制度/地名/数値/語義は正確に(不確かなら自分で確認)。' : ''}
出力は指定スキーマJSONのみ。`
}
function solvePrompt(u, blind, lens) {
  const lensText = { A: '自力で最後まで解いてから選ぶ。', B: '各選択肢を点検し2正解/条件不足でないか厳しく確認。曖昧なら false。', fact: '事実(年号/人名/制度/地名/数値/語義/法則)は不確かなら WebSearch(必要なら ToolSearch で有効化)で裏取りして選ぶ。' }[lens]
  return `中学「${SUBJECT}」単元「${u.filter}」の4択問題を正解を伏せて独立に解答。各設問の最も正しい0始indexを選び answers[{i,choice_index,confident}] を返す。${lensText}
設問(JSON {i,stem,choices}):
${JSON.stringify(blind, null, 1)}
出力は指定スキーマJSONのみ。`
}

const results = await pipeline(
  UNITS,
  async (u) => {
    const out = await agent(authorPrompt(u), { label: `author:${PART}/${u.filter}`, phase: 'Author', schema: AUTHOR_SCHEMA })
    return { u, questions: (out && Array.isArray(out.questions)) ? out.questions : [] }
  },
  async (prev) => {
    const { u, questions } = prev
    if (!questions.length) return { gi: u.gi, filter: u.filter, need: u.need, kept: [] }
    const blind = questions.map((q, i) => ({ i, stem: q.stem, choices: q.choices }))
    const lenses = u.factcheck ? ['A', 'B', 'fact'] : ['A', 'B', 'A']
    const solvers = await parallel(lenses.map((lens, k) => () => agent(solvePrompt(u, blind, lens), { label: `solve${k}:${PART}/${u.filter}`, phase: 'Verify', schema: SOLVE_SCHEMA, agentType: 'general-purpose', effort: lens === 'fact' ? 'high' : 'medium' })))
    const idxOf = (res, i) => { const a = res?.answers?.find((x) => x.i === i); return a ? { ci: a.choice_index, conf: a.confident } : null }
    const kept = []
    for (let i = 0; i < questions.length; i++) {
      const q = questions[i]
      if (new Set(q.choices.map((c) => String(c).trim())).size !== 4) continue
      const rs = solvers.map((s) => idxOf(s, i))
      if (rs.some((r) => !r)) continue
      if (!rs.every((r) => r.ci === q.answer_index && r.conf)) continue
      kept.push({ subject: SUBJECT, part: PART, filter: u.filter, unit: u.filter, stem: q.stem, passage: '', choices: q.choices, answer_index: q.answer_index, explanation: q.explanation })
    }
    const capped = kept.slice(0, u.need)
    log(`${PART}/${u.filter}: authored=${questions.length} 一致=${kept.length} 採用=${capped.length}/${u.need}`)
    return { gi: u.gi, filter: u.filter, need: u.need, kept: capped }
  }
)

return { part: PART, units: results.filter(Boolean), totalKept: results.filter(Boolean).reduce((a, r) => a + (r.kept ? r.kept.length : 0), 0) }
