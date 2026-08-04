export const meta = {
  name: 'chugaku-gen-expand',
  description: '中学ドリル(英/国/理/社)の非読解単元を各24問へ増量。既存stem回避で作問→3独立盲ソルバー(事実科目は1名WebSearch裏取り)全員一致のみ採用。',
  phases: [
    { title: 'Author', detail: '既存stem回避で作問' },
    { title: 'Verify', detail: '3独立盲ソルバー(事実科目はWebSearch裏取り)' },
  ],
}

const A = typeof args === 'string' ? JSON.parse(args) : args
const PART = A.part, SUBJECT = A.subject
const UNITS = A.units   // [{filter, gi, gen, factcheck}]

const SUBJ_HINT = {
  '英語': '公立高校入試 標準の文法・語法・適語補充・語形変化・対話応答。ネイティブが認める正解が1つに定まる問題のみ(2正解・曖昧禁止)。stem/選択肢に英語を使い、問い方の指示は日本語でよい。図・音声・本文なしで解ける自己完結問題。',
  '国語': `中学国語の知識問題(単元「__F__」に対応: 漢字の読み書き/語句・慣用句・ことわざ・四字熟語/文法=品詞・活用・文の成分/敬語=尊敬・謙譲・丁寧/古文の基礎=古語の意味・歴史的仮名遣い・係り結び・基本文法/詩・短歌・俳句の知識と表現技法=季語・切れ字・比喩・体言止め等)。本文がなくても解ける自己完結問題。諸説ある/高校範囲は避け、教科書レベルの定説のみ。古文の引用は短い有名古典の一節に留める。`,
  '理科': '中学理科の教科書事実のみ。用語・法則・数値・単位・実験結果・グラフの読みを正確に。図が必須の問題は避け、必要な数値や条件はすべて文章で与える(自己完結)。高校範囲・諸説ある事項は出さない。',
  '社会': '中学社会の教科書事実のみ(公立入試頻出)。年号・人名・制度・地名・出来事の因果・統計を正確に。諸説ある/細かすぎる/時事で変動する事項は避ける。図なしで解ける自己完結問題。',
}

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
  const hint = (SUBJ_HINT[SUBJECT] || '').replace('__F__', u.filter)
  return `あなたは公立高校入試 標準レベル(中1〜中3)の「${SUBJECT}」作問のプロです。単元「${u.filter}」の4択問題を ${u.gen} 問つくってください。
【重複回避(最重要)】まず Read ツールで scripts/chugaku_dojo/add2/_stems_${PART}.json のキー「${u.filter}」(本番既存の問題文)を読み、同じ設定・同じ問い方の重複を避ける。数値・語・文脈を変え、単元内の別パターンも積極的にカバーする。
【教科の要点】${hint}
【厳守】
1. 4択・正解ちょうど1つ・一意(2正解/0正解/曖昧は禁止)。誤答は中学生が実際にやる典型ミス(荒唐無稽禁止)。
2. answer_index=正解の0始index。choices は4つとも相異なる文字列。
3. ★選択肢に「正解と同じ意味・同じ値になるもの」を入れない(=2正解になる)。
4. unit は厳密に "${u.filter}"。図・本文なしで解ける自己完結。事実・数値・語形は厳密に正確に。
5. explanation は 【単元】${u.filter}。正解は「<正解選択肢の文字列そのまま>」。 で始め、中学生向けの短い解説(理由・根拠・年号や語義など値のみ)。★「ア/A/①/N番目」等の位置表記は絶対に書かない(値・語で説明)。
${u.factcheck ? '6. ★事実の厳密性: 年号・人名・制度・地名・数値・語義・活用など、少しでも不確かなものは自分で確認してから出す。中学教科書の定説と一致させる。' : ''}
出力は指定スキーマJSONのみ。`
}

function solvePrompt(u, blind, lens) {
  const head = `中学「${SUBJECT}」単元「${u.filter}」の4択問題を、正解を伏せた状態で独立に解答します。各設問の最も正しい選択肢の0始まりindexを1つ選び answers[{i,choice_index,confident}] を返す。confident=一意に正しいと確信できるか(曖昧/2正解の疑いは false)。`
  const lensText = {
    A: '自力で最後まで解いてから答えを選ぶ。',
    B: '各選択肢を1つずつ検討し「2つ正解/どれも不適/条件不足」でないか厳しく点検してから唯一の正解を選ぶ。少しでも曖昧なら false。',
    fact: 'あなたは事実照合者です。年号・人名・制度・地名・数値・語義・法則・実験結果などは、少しでも不確かなら WebSearch(必要なら ToolSearch で有効化)で裏取りしてから、事実として正しい選択肢を選ぶ。confident=裏取りできたか。',
  }[lens]
  return `${head}
${lensText}

設問(JSON配列 {i,stem,choices}):
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
    if (!questions.length) return { gi: u.gi, filter: u.filter, add: u.add, kept: [], authored: 0 }
    const blind = questions.map((q, i) => ({ i, stem: q.stem, choices: q.choices }))
    const lenses = u.factcheck ? ['A', 'B', 'fact'] : ['A', 'B', 'C_reason']
    const tasks = lenses.map((lens) => () => agent(
      solvePrompt(u, blind, lens === 'C_reason' ? 'A' : lens),
      { label: `solve${lens}:${PART}/${u.filter}`, phase: 'Verify', schema: SOLVE_SCHEMA, agentType: 'general-purpose', effort: (lens === 'fact') ? 'high' : 'medium' },
    ))
    const solvers = await parallel(tasks)
    const idxOf = (res, i) => { const a = res?.answers?.find((x) => x.i === i); return a ? { ci: a.choice_index, conf: a.confident } : null }
    const kept = []
    let dA = 0, dC = 0
    for (let i = 0; i < questions.length; i++) {
      const q = questions[i]
      if (new Set(q.choices.map((c) => String(c).trim())).size !== 4) continue
      const rs = solvers.map((s) => idxOf(s, i))
      if (rs.some((r) => !r)) { dA++; continue }
      if (!rs.every((r) => r.ci === q.answer_index)) { dA++; continue }
      if (!rs.every((r) => r.conf)) { dC++; continue }
      kept.push({ subject: SUBJECT, part: PART, filter: u.filter, unit: u.filter, stem: q.stem, passage: '', choices: q.choices, answer_index: q.answer_index, explanation: q.explanation })
    }
    const capped = kept.slice(0, u.add)
    log(`${PART}/${u.filter}: authored=${questions.length} 一致=${kept.length} 採用=${capped.length}/${u.add} (drop不一致${dA}/自信${dC})`)
    return { gi: u.gi, filter: u.filter, add: u.add, authored: questions.length, agreed: kept.length, kept: capped }
  }
)

const flat = results.filter(Boolean)
const totalKept = flat.reduce((a, r) => a + (r.kept ? r.kept.length : 0), 0)
const shorts = flat.filter((r) => (r.kept ? r.kept.length : 0) < r.add).map((r) => `${r.filter}:${r.kept.length}/${r.add}`)
log(`GEN DONE ${PART} totalKept=${totalKept} shorts=[${shorts.join(', ')}]`)
return { part: PART, units: flat, totalKept, shorts }
