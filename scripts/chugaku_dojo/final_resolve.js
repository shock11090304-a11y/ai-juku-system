export const meta = {
  name: 'chugaku-math-final-resolve',
  description: '投入後の最終盲再解答: DBに保存された211問(add/_stored_blind.json, 正解伏せ)を単元ごと2独立ソルバー(1名Python計算)が解き、保存キーとの一致を確認するための解答を返す。',
  phases: [{ title: 'ReSolve', detail: '保存済データを盲で再解答' }],
}

const UNITS = [
  '正負の数', '式の計算', '一次方程式', '連立方程式', '平方根', '二次方程式', '比例・反比例',
  '一次関数', '二乗に比例', '合同と証明', '相似', '円周角', '三平方の定理', '確率', 'データの活用',
]
const BLIND = 'scripts/chugaku_dojo/add/_stored_blind.json'

const SCHEMA = {
  type: 'object', additionalProperties: false, required: ['answers'],
  properties: {
    answers: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false, required: ['gid', 'choice_index', 'confident'],
        properties: { gid: { type: 'string' }, choice_index: { type: 'integer', minimum: 0, maximum: 3 }, confident: { type: 'boolean' } },
      },
    },
  },
}

function prompt(filter, lens) {
  const lensText = lens === 'py'
    ? '可能な限り Bash で python3 を実行し、実際に数値計算・全列挙・方程式の求解をして正解を確定する。'
    : '自力で最後まで計算・推論してから答えを選ぶ。'
  return `ファイル ${BLIND} を Read ツールで読んでください(JSON配列 {gid, unit, stem, choices})。unit === "${filter}" の設問だけを対象に、各設問を正解を伏せた状態で独立に解答します。
${lensText}
各設問について最も正しい選択肢の0始まりindex(choices内の位置)を1つ選び、answers[{gid, choice_index, confident}] を返す。confident=一意に確信できるか。
出力は指定スキーマJSONのみ。`
}

const out = await parallel(
  UNITS.map((filter) => async () => {
    const [a, b] = await parallel([
      () => agent(prompt(filter, 'reason'), { label: `re:${filter}`, phase: 'ReSolve', schema: SCHEMA, agentType: 'general-purpose' }),
      () => agent(prompt(filter, 'py'), { label: `py:${filter}`, phase: 'ReSolve', schema: SCHEMA, agentType: 'general-purpose', effort: 'high' }),
    ])
    const merge = (r) => (r && Array.isArray(r.answers)) ? r.answers : []
    return { filter, solverA: merge(a), solverB: merge(b) }
  })
)

return { units: out.filter(Boolean) }
