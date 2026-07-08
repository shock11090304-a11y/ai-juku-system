export const meta = {
  name: 'chugaku-math-expand',
  description: '中学数学ドリル15単元を各24問へ増量。既存stemを避けて作問→3独立盲ソルバー(1名はPython数値計算)全員一致のみ採用→add/math__<gi>.json 保存用に返す。',
  phases: [
    { title: 'Author', detail: '既存stemを避け各単元を多めに作問' },
    { title: 'Verify', detail: '3独立盲ソルバー全員一致(Python計算含む)で選別' },
  ],
}

// current=既存件数, add=目標追加数(→24), gen=作問数(採用余裕込み)
const UNITS = [
  { filter: '正負の数',     gi: 13, current: 10, add: 14, gen: 20 },
  { filter: '式の計算',     gi: 14, current: 10, add: 14, gen: 20 },
  { filter: '一次方程式',   gi: 15, current: 10, add: 14, gen: 20 },
  { filter: '連立方程式',   gi: 16, current: 10, add: 14, gen: 20 },
  { filter: '平方根',       gi: 17, current: 10, add: 14, gen: 20 },
  { filter: '二次方程式',   gi: 18, current: 10, add: 14, gen: 20 },
  { filter: '比例・反比例', gi: 19, current: 10, add: 14, gen: 20 },
  { filter: '一次関数',     gi: 20, current: 10, add: 14, gen: 20 },
  { filter: '二乗に比例',   gi: 21, current: 10, add: 14, gen: 20 },
  { filter: '合同と証明',   gi: 22, current: 10, add: 14, gen: 20 },
  { filter: '相似',         gi: 23, current: 10, add: 14, gen: 20 },
  { filter: '円周角',       gi: 24, current: 9,  add: 15, gen: 22 },
  { filter: '三平方の定理', gi: 25, current: 10, add: 14, gen: 20 },
  { filter: '確率',         gi: 26, current: 10, add: 14, gen: 20 },
  { filter: 'データの活用', gi: 27, current: 10, add: 14, gen: 20 },
]

const AUTHOR_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['questions'],
  properties: {
    questions: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        required: ['stem', 'choices', 'answer_index', 'unit', 'explanation'],
        properties: {
          stem: { type: 'string' },
          choices: { type: 'array', items: { type: 'string' }, minItems: 4, maxItems: 4 },
          answer_index: { type: 'integer', minimum: 0, maximum: 3 },
          unit: { type: 'string' },
          explanation: { type: 'string' },
        },
      },
    },
  },
}
const SOLVE_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['answers'],
  properties: {
    answers: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false, required: ['i', 'choice_index', 'confident'],
        properties: {
          i: { type: 'integer' },
          choice_index: { type: 'integer', minimum: 0, maximum: 3 },
          confident: { type: 'boolean' },
        },
      },
    },
  },
}

function authorPrompt(u) {
  return `あなたは公立高校入試(標準・中1〜中3)の数学作問のプロです。単元「${u.filter}」の4択問題を ${u.gen} 問つくってください。

【重複回避(最重要)】
- まず Read ツールで scripts/chugaku_dojo/add/_existing_stems.json を読み、キー「${u.filter}」の配列(既存問題文)を確認する。
- 既存と「同じ数値・同じ設定」の問題は禁止。数値・文脈・問い方を変え、単元内の別パターンも積極的にカバーして重複しないようにする。

【厳守】
1. 4択・正解ちょうど1つ・一意(2正解/0正解/曖昧は禁止)。誤答は中学生が実際にやる典型ミスの値にする(荒唐無稽禁止)。
2. answer_index = 正解の0始まりindex。choices は4つとも異なる文字列。
3. unit フィールドは厳密に "${u.filter}"。
4. 図がないと解けない問題は出さない。必要な条件はすべて stem の文章に書く(自己完結)。数値・単位・計算は厳密に。
5. explanation は必ず 【単元】${u.filter}。正解は「<正解選択肢の文字列そのまま>」。 で始め、中学生向けの短い解説(途中式や理由・値のみ)を続ける。
   ★explanation に「ア/イ」「A/B」「①」「N番目」「選択肢の◯」など"位置"を指す表現を絶対に書かない(値・式のみ)。位置表記はシャッフルで解説が壊れるため厳禁。
6. 基本〜標準〜やや応用をバランスよく。単元全体を偏りなくカバー。
出力は指定スキーマJSONのみ。`
}

function solvePrompt(u, blind, lens) {
  const head = `中学数学「${u.filter}」の4択問題を、正解を伏せた状態で独立に解答します。各設問について、最も正しい選択肢の0始まりindexを1つ選び、answers[{i,choice_index,confident}] を返してください。confident=一意に正しいと確信できるか(曖昧・2正解の疑いがあれば false)。`
  const lensText = {
    A: '自力で最後まで計算・推論してから答えを選ぶこと。',
    B: '各選択肢を1つずつ検討し、「正解が2つある/どれも当てはまらない/条件不足」でないかを厳しく点検してから、唯一の正解を選ぶこと。少しでも曖昧なら confident=false。',
    C: '可能な限り Bash ツールで python3 を実行し、実際に数値計算・場合の数の全列挙・方程式の解などを計算して正解を確定させること(例: python3 -c "..."). 計算で一意に決まらなければ confident=false。',
  }[lens]
  return `${head}
${lensText}

設問(JSON配列 {i,stem,choices}):
${JSON.stringify(blind, null, 1)}

出力は指定スキーマJSONのみ(answers)。`
}

const results = await pipeline(
  UNITS,
  // Phase 1: 作問
  async (u) => {
    const out = await agent(authorPrompt(u), { label: `author:${u.filter}`, phase: 'Author', schema: AUTHOR_SCHEMA })
    const qs = (out && Array.isArray(out.questions)) ? out.questions : []
    return { u, questions: qs }
  },
  // Phase 2: 3独立盲ソルバー全員一致で選別
  async (prev) => {
    const { u, questions } = prev
    if (!questions.length) return { filter: u.filter, gi: u.gi, add: u.add, kept: [], authored: 0, note: 'author empty' }
    const blind = questions.map((q, i) => ({ i, stem: q.stem, choices: q.choices }))
    const solvers = await parallel([
      () => agent(solvePrompt(u, blind, 'A'), { label: `solveA:${u.filter}`, phase: 'Verify', schema: SOLVE_SCHEMA, agentType: 'general-purpose' }),
      () => agent(solvePrompt(u, blind, 'B'), { label: `solveB:${u.filter}`, phase: 'Verify', schema: SOLVE_SCHEMA, agentType: 'general-purpose' }),
      () => agent(solvePrompt(u, blind, 'C'), { label: `solveC:${u.filter}`, phase: 'Verify', schema: SOLVE_SCHEMA, agentType: 'general-purpose', effort: 'high' }),
    ])
    const idxOf = (res, i) => {
      if (!res || !Array.isArray(res.answers)) return null
      const a = res.answers.find((x) => x.i === i)
      return a ? { ci: a.choice_index, conf: a.confident } : null
    }
    const kept = []
    let dropAgree = 0, dropConf = 0, dropDupIdx = 0
    for (let i = 0; i < questions.length; i++) {
      const q = questions[i]
      // 選択肢重複ガード(念のため)
      const uniq = new Set(q.choices.map((c) => String(c).trim()))
      if (uniq.size !== 4) { dropDupIdx++; continue }
      const a = idxOf(solvers[0], i), b = idxOf(solvers[1], i), c = idxOf(solvers[2], i)
      if (!a || !b || !c) { dropAgree++; continue }
      const allAgree = a.ci === q.answer_index && b.ci === q.answer_index && c.ci === q.answer_index
      if (!allAgree) { dropAgree++; continue }
      if (!(a.conf && b.conf && c.conf)) { dropConf++; continue }
      kept.push({
        subject: '数学', part: 'math', filter: u.filter, unit: u.filter,
        stem: q.stem, passage: '', choices: q.choices, answer_index: q.answer_index,
        explanation: q.explanation,
      })
    }
    const capped = kept.slice(0, u.add)
    log(`${u.filter}: authored=${questions.length} 全員一致=${kept.length} 採用=${capped.length}/${u.add} (drop: 不一致${dropAgree}/自信${dropConf}/重複${dropDupIdx})`)
    return { filter: u.filter, gi: u.gi, add: u.add, authored: questions.length, agreed: kept.length, kept: capped }
  }
)

const flat = results.filter(Boolean)
const totalKept = flat.reduce((a, r) => a + (r.kept ? r.kept.length : 0), 0)
const shorts = flat.filter((r) => (r.kept ? r.kept.length : 0) < r.add).map((r) => `${r.filter}:${r.kept.length}/${r.add}`)
log(`DONE totalKept=${totalKept} shorts=[${shorts.join(', ')}]`)
return { units: flat, totalKept, shorts }
