export const meta = {
  name: 'chugaku-gen-reading',
  description: '読解単元(英語 長文読解 / 国語 説明的文章・文学的文章)を各24問へ。オリジナル本文+本文依拠の4択を作問→本文込み3独立盲ソルバー全員一致のみ採用。',
  phases: [
    { title: 'Author', detail: 'オリジナル本文+設問を作問' },
    { title: 'Verify', detail: '本文込み3独立盲ソルバー全員一致' },
  ],
}

const A = typeof args === 'string' ? JSON.parse(args) : args
const UNITS = A.units.map((u) => ({ ...u, gen: u.gen || (u.add + 6) }))

const AUTHOR_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['passages'],
  properties: {
    passages: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false, required: ['passage', 'questions'],
        properties: {
          passage: { type: 'string' },
          questions: {
            type: 'array',
            items: {
              type: 'object', additionalProperties: false, required: ['stem', 'choices', 'answer_index', 'explanation'],
              properties: {
                stem: { type: 'string' },
                choices: { type: 'array', items: { type: 'string' }, minItems: 4, maxItems: 4 },
                answer_index: { type: 'integer', minimum: 0, maximum: 3 },
                explanation: { type: 'string' },
              },
            },
          },
        },
      },
    },
  },
}
const SOLVE_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['answers'],
  properties: {
    answers: { type: 'array', items: { type: 'object', additionalProperties: false, required: ['i', 'choice_index', 'confident'], properties: { i: { type: 'integer' }, choice_index: { type: 'integer', minimum: 0, maximum: 3 }, confident: { type: 'boolean' } } } },
  },
}

const HINT = {
  '長文読解': '中学英語の長文読解。1本あたり120〜200語程度のオリジナル英文パッセージ(日常・学校・環境・人物紹介など平易な題材)を複数作り、各パッセージにつき本文の内容に関する4択問題を4〜5問。設問・選択肢は英語でよいが、問い方の指示は日本語でもよい。',
  '説明的文章': '中学国語の説明的文章(説明文・評論)。1本あたり300〜450字程度のオリジナル説明文を複数作り、各本文につき内容理解・指示語の指す内容・接続語・筆者の主張(要旨)に関する4択問題を4〜5問。',
  '文学的文章': '中学国語の文学的文章(小説・随筆の一場面)。1本あたり300〜450字程度のオリジナルの物語/随筆を複数作り、各本文につき登場人物の心情・情景・行動の理由・表現の工夫に関する4択問題を4〜5問。',
}

function authorPrompt(u) {
  return `あなたは公立高校入試 標準の「${u.subject}・${u.filter}」の作問のプロです。合計で ${u.gen} 問以上になるように、本文(パッセージ)と設問のセットを複数つくってください。
【教科の要点】${HINT[u.filter] || ''}
【著作権・厳守】
1. 本文は必ず"完全オリジナル"。既存の小説・評論・教科書・新聞記事など実在著作物の引用・改変は禁止(著作権)。固有の作品名・実在人物の文章は使わない。
2. 各設問は「本文だけを根拠に、客観的に正解が1つに定まる」ものにする(主観的な深読み・本文外の知識が要るものは不可)。2正解・曖昧は禁止。
3. choices は4つとも相異なり、正解と同義・同値の選択肢を入れない。answer_index=正解の0始index。
4. explanation は 【単元】${u.filter}。正解は「<正解選択肢の文字列そのまま>」。 で始め、本文のどこからそう言えるかを短く示す(位置表記 ア/A/①/N番目 は禁止・値/根拠で)。
5. 1つの passage に questions を 4〜5問ずつ入れる。passage は各セットで別内容にする。
出力は指定スキーマJSONのみ。`
}

function solvePrompt(u, passage, blind, lens) {
  const lensText = lens === 'B' ? '各選択肢を本文と照合し、2つ正解/本文に根拠なし/曖昧でないか厳しく点検する。曖昧なら false。' : '本文をよく読み、本文の記述だけを根拠に答えを選ぶ。'
  return `中学「${u.subject}・${u.filter}」の読解問題です。次の本文を読み、正解を伏せた各設問に独立に解答してください。本文に書かれていることだけを根拠にする(本文外の知識で判断しない)。${lensText}

【本文】
${passage}

【設問】(JSON配列 {i,stem,choices})
${JSON.stringify(blind, null, 1)}

各設問の最も正しい選択肢の0始まりindexを answers[{i,choice_index,confident}] で返す。出力は指定スキーマJSONのみ。`
}

const results = await pipeline(
  UNITS,
  async (u) => {
    const out = await agent(authorPrompt(u), { label: `author:${u.part}/${u.filter}`, phase: 'Author', schema: AUTHOR_SCHEMA })
    const passages = (out && Array.isArray(out.passages)) ? out.passages : []
    return { u, passages }
  },
  async (prev) => {
    const { u, passages } = prev
    const kept = []
    for (const pg of passages) {
      const qs = Array.isArray(pg.questions) ? pg.questions : []
      if (!qs.length || !(pg.passage || '').trim()) continue
      const blind = qs.map((q, i) => ({ i, stem: q.stem, choices: q.choices }))
      const solvers = await parallel([
        () => agent(solvePrompt(u, pg.passage, blind, 'A'), { label: `solveA:${u.filter}`, phase: 'Verify', schema: SOLVE_SCHEMA, agentType: 'general-purpose' }),
        () => agent(solvePrompt(u, pg.passage, blind, 'B'), { label: `solveB:${u.filter}`, phase: 'Verify', schema: SOLVE_SCHEMA, agentType: 'general-purpose' }),
        () => agent(solvePrompt(u, pg.passage, blind, 'C'), { label: `solveC:${u.filter}`, phase: 'Verify', schema: SOLVE_SCHEMA, agentType: 'general-purpose', effort: 'high' }),
      ])
      const idxOf = (r, i) => { const a = r?.answers?.find((x) => x.i === i); return a ? { ci: a.choice_index, conf: a.confident } : null }
      for (let i = 0; i < qs.length; i++) {
        const q = qs[i]
        if (new Set(q.choices.map((c) => String(c).trim())).size !== 4) continue
        const rs = solvers.map((s) => idxOf(s, i))
        if (rs.some((r) => !r)) continue
        if (!rs.every((r) => r.ci === q.answer_index && r.conf)) continue
        kept.push({ subject: u.subject, part: u.part, filter: u.filter, unit: u.filter, stem: q.stem, passage: pg.passage, choices: q.choices, answer_index: q.answer_index, explanation: q.explanation })
      }
    }
    const capped = kept.slice(0, u.add)
    log(`${u.part}/${u.filter}: passages=${passages.length} 一致=${kept.length} 採用=${capped.length}/${u.add}`)
    return { gi: u.gi, filter: u.filter, add: u.add, kept: capped }
  }
)

const flat = results.filter(Boolean)
return { part: A.part || 'mixed', units: flat, totalKept: flat.reduce((a, r) => a + (r.kept ? r.kept.length : 0), 0) }
