export const meta = {
  name: 'chugaku-math-topup',
  description: 'DROPで不足した単元だけ追加生成。既存DB stem + 既存addファイル stem を避けて作問→3独立盲ソルバー全員一致(1名Python計算)→不足数だけ採用して返す。',
  phases: [
    { title: 'Author', detail: '不足単元を既存全stem回避で作問' },
    { title: 'Verify', detail: '3独立盲ソルバー全員一致で選別' },
  ],
}

// args = [{gi, filter, need}]  (need = あと何問必要か)
const _args = typeof args === 'string' ? JSON.parse(args) : args
const UNITS = (Array.isArray(_args) ? _args : []).map((u) => ({ ...u, gen: Math.max(6, Math.ceil(u.need * 2)) }))

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
          unit: { type: 'string' }, explanation: { type: 'string' },
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
        properties: { i: { type: 'integer' }, choice_index: { type: 'integer', minimum: 0, maximum: 3 }, confident: { type: 'boolean' } },
      },
    },
  },
}

function authorPrompt(u) {
  return `あなたは公立高校入試(標準)の数学作問のプロです。単元「${u.filter}」の4択問題を ${u.gen} 問つくってください。
【重複回避(最重要)】まず Read ツールで次の2ファイルを読み、既出の問題文と重複しない新問だけを作る:
 - scripts/chugaku_dojo/add/_existing_stems.json のキー「${u.filter}」(本番既存)
 - scripts/chugaku_dojo/add/math__${u.gi}.json (今回追加済み。存在すれば各要素の stem)
数値・文脈・問い方を変え、単元内の別パターンもカバーすること。
${u.note ? '【単元範囲】' + u.note + '\n' : ''}【厳守】
1. 4択・正解ちょうど1つ・一意。誤答は中学生が実際にやる典型ミスの値。
2. answer_index=正解の0始index、choices4つは相異なる。
3. ★【選択肢の"同値"を厳禁】4つの選択肢は互いに『数学的に異なる値』にすること。簡約すると一致する表現を混ぜてはいけない。例:『5√2』と『√50』は同値、『±7』と『±√49』は同値、『±3』と『±√9』は同値、『2√5』と『10√5/5』は同値、『6』と『√36』は同値。正解の値と等しくなる選択肢を1つでも作ると"2正解"になり不合格。誤答は正解と明確に異なる数値にする。**必ず Bash で python3 を実行し、4つの選択肢を数値化(平方根・分数も float 化)して、正解以外の選択肢が正解と一致しないことを確認してから提出する**。
4. unit は厳密に "${u.filter}"。
5. 図なしで解ける自己完結。数値・単位は厳密に。
6. ★【解説の検算】explanation は 【単元】${u.filter}。正解は「<正解選択肢の文字列そのまま>」。 で始め、値のみの短い解説(位置表記ア/A/①/N番目は厳禁)。解説中の『たして/かけて/=/途中式』の数値は必ず正しいものにする(符号ミス厳禁。例:『たして8・かけて15の2数』は 3と5 であって −3,−5 ではない)。
出力は指定スキーマJSONのみ。`
}
function solvePrompt(u, blind, lens) {
  const lensText = {
    A: '自力で最後まで計算・推論してから答えを選ぶ。',
    B: '各選択肢を1つずつ検討し2正解/条件不足でないか厳しく点検。曖昧なら confident=false。',
    C: '可能な限り Bash で python3 を実行して数値計算・全列挙・求解し正解を確定。一意に決まらなければ confident=false。',
  }[lens]
  return `中学数学「${u.filter}」の4択問題を正解を伏せて独立に解答します。各設問の最も正しい選択肢の0始indexを1つ選び answers[{i,choice_index,confident}] を返す。${lensText}
設問(JSON配列 {i,stem,choices}):
${JSON.stringify(blind, null, 1)}
出力は指定スキーマJSONのみ。`
}

const results = await pipeline(
  UNITS,
  async (u) => {
    const out = await agent(authorPrompt(u), { label: `author:${u.filter}`, phase: 'Author', schema: AUTHOR_SCHEMA })
    return { u, questions: (out && Array.isArray(out.questions)) ? out.questions : [] }
  },
  async (prev) => {
    const { u, questions } = prev
    if (!questions.length) return { gi: u.gi, filter: u.filter, need: u.need, kept: [] }
    const blind = questions.map((q, i) => ({ i, stem: q.stem, choices: q.choices }))
    const solvers = await parallel([
      () => agent(solvePrompt(u, blind, 'A'), { label: `solveA:${u.filter}`, phase: 'Verify', schema: SOLVE_SCHEMA, agentType: 'general-purpose' }),
      () => agent(solvePrompt(u, blind, 'B'), { label: `solveB:${u.filter}`, phase: 'Verify', schema: SOLVE_SCHEMA, agentType: 'general-purpose' }),
      () => agent(solvePrompt(u, blind, 'C'), { label: `solveC:${u.filter}`, phase: 'Verify', schema: SOLVE_SCHEMA, agentType: 'general-purpose', effort: 'high' }),
    ])
    const idxOf = (res, i) => { const a = res?.answers?.find((x) => x.i === i); return a ? { ci: a.choice_index, conf: a.confident } : null }
    const kept = []
    for (let i = 0; i < questions.length; i++) {
      const q = questions[i]
      if (new Set(q.choices.map((c) => String(c).trim())).size !== 4) continue
      const a = idxOf(solvers[0], i), b = idxOf(solvers[1], i), c = idxOf(solvers[2], i)
      if (!a || !b || !c) continue
      if (!(a.ci === q.answer_index && b.ci === q.answer_index && c.ci === q.answer_index)) continue
      if (!(a.conf && b.conf && c.conf)) continue
      kept.push({ subject: '数学', part: 'math', filter: u.filter, unit: u.filter, stem: q.stem, passage: '', choices: q.choices, answer_index: q.answer_index, explanation: q.explanation })
    }
    const capped = kept.slice(0, u.need)
    log(`${u.filter}: authored=${questions.length} 一致=${kept.length} 採用=${capped.length}/${u.need}`)
    return { gi: u.gi, filter: u.filter, need: u.need, kept: capped }
  }
)

const flat = results.filter(Boolean)
return { units: flat, totalKept: flat.reduce((a, r) => a + (r.kept ? r.kept.length : 0), 0) }
