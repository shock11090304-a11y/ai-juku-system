export const meta = {
  name: 'chugaku-dojo-gen',
  description: '中学生(公立高校入試 標準)入試問題道場 弱点克服ドリルを単元別に作問→3独立盲ソルバー全員一致→社会理科は事実監査→検証済のみディスク保存',
  phases: [
    { title: 'Author', detail: '単元ごとに10問前後を作問(自己完結4択)' },
    { title: 'Verify', detail: '3独立盲ソルバー全員一致 + 社会/理科は事実監査' },
    { title: 'Persist', detail: '検証通過のみ verified/*.json へ保存' },
  ],
}

// 単元カタログを埋め込み(args依存を排除・再現性のため units.json 由来)。
const UNITS = [{"subject": "英語", "part": "eng", "filter": "be動詞・一般動詞", "name": "be動詞・一般動詞", "reading": false, "factcheck": false, "n": 10}, {"subject": "英語", "part": "eng", "filter": "時制", "name": "時制（過去・進行・未来）", "reading": false, "factcheck": false, "n": 10}, {"subject": "英語", "part": "eng", "filter": "助動詞", "name": "助動詞", "reading": false, "factcheck": false, "n": 10}, {"subject": "英語", "part": "eng", "filter": "名詞・代名詞・冠詞", "name": "名詞・代名詞・冠詞", "reading": false, "factcheck": false, "n": 10}, {"subject": "英語", "part": "eng", "filter": "比較", "name": "比較", "reading": false, "factcheck": false, "n": 10}, {"subject": "英語", "part": "eng", "filter": "不定詞・動名詞", "name": "不定詞・動名詞", "reading": false, "factcheck": false, "n": 10}, {"subject": "英語", "part": "eng", "filter": "分詞", "name": "分詞（現在分詞・過去分詞）", "reading": false, "factcheck": false, "n": 10}, {"subject": "英語", "part": "eng", "filter": "受動態", "name": "受動態", "reading": false, "factcheck": false, "n": 10}, {"subject": "英語", "part": "eng", "filter": "現在完了", "name": "現在完了", "reading": false, "factcheck": false, "n": 10}, {"subject": "英語", "part": "eng", "filter": "関係代名詞", "name": "関係代名詞", "reading": false, "factcheck": false, "n": 10}, {"subject": "英語", "part": "eng", "filter": "接続詞・前置詞", "name": "接続詞・前置詞", "reading": false, "factcheck": false, "n": 10}, {"subject": "英語", "part": "eng", "filter": "会話表現", "name": "会話・熟語表現", "reading": false, "factcheck": false, "n": 10}, {"subject": "英語", "part": "eng", "filter": "長文読解", "name": "長文読解", "reading": true, "factcheck": false, "n": 9}, {"subject": "数学", "part": "math", "filter": "正負の数", "name": "正負の数・四則計算", "reading": false, "factcheck": false, "n": 10}, {"subject": "数学", "part": "math", "filter": "式の計算", "name": "文字式・式の計算", "reading": false, "factcheck": false, "n": 10}, {"subject": "数学", "part": "math", "filter": "一次方程式", "name": "一次方程式・文章題", "reading": false, "factcheck": false, "n": 10}, {"subject": "数学", "part": "math", "filter": "連立方程式", "name": "連立方程式", "reading": false, "factcheck": false, "n": 10}, {"subject": "数学", "part": "math", "filter": "平方根", "name": "平方根", "reading": false, "factcheck": false, "n": 10}, {"subject": "数学", "part": "math", "filter": "二次方程式", "name": "二次方程式", "reading": false, "factcheck": false, "n": 10}, {"subject": "数学", "part": "math", "filter": "比例・反比例", "name": "比例・反比例", "reading": false, "factcheck": false, "n": 10}, {"subject": "数学", "part": "math", "filter": "一次関数", "name": "一次関数", "reading": false, "factcheck": false, "n": 10}, {"subject": "数学", "part": "math", "filter": "二乗に比例", "name": "関数 y=ax²（二乗に比例）", "reading": false, "factcheck": false, "n": 10}, {"subject": "数学", "part": "math", "filter": "合同と証明", "name": "三角形の合同と証明", "reading": false, "factcheck": false, "n": 10}, {"subject": "数学", "part": "math", "filter": "相似", "name": "図形の相似", "reading": false, "factcheck": false, "n": 10}, {"subject": "数学", "part": "math", "filter": "円周角", "name": "円周角", "reading": false, "factcheck": false, "n": 10}, {"subject": "数学", "part": "math", "filter": "三平方の定理", "name": "三平方の定理", "reading": false, "factcheck": false, "n": 10}, {"subject": "数学", "part": "math", "filter": "確率", "name": "場合の数・確率", "reading": false, "factcheck": false, "n": 10}, {"subject": "数学", "part": "math", "filter": "データの活用", "name": "データの活用（統計）", "reading": false, "factcheck": false, "n": 10}, {"subject": "国語", "part": "kokugo", "filter": "漢字", "name": "漢字の読み書き", "reading": false, "factcheck": false, "n": 10}, {"subject": "国語", "part": "kokugo", "filter": "語句", "name": "語句・慣用句・四字熟語", "reading": false, "factcheck": false, "n": 10}, {"subject": "国語", "part": "kokugo", "filter": "文法", "name": "文法（品詞・活用）", "reading": false, "factcheck": false, "n": 10}, {"subject": "国語", "part": "kokugo", "filter": "敬語", "name": "敬語", "reading": false, "factcheck": false, "n": 10}, {"subject": "国語", "part": "kokugo", "filter": "古文", "name": "古文入門", "reading": false, "factcheck": false, "n": 10}, {"subject": "国語", "part": "kokugo", "filter": "詩歌", "name": "詩・短歌・俳句", "reading": false, "factcheck": false, "n": 10}, {"subject": "国語", "part": "kokugo", "filter": "説明的文章", "name": "説明的文章の読解", "reading": true, "factcheck": false, "n": 9}, {"subject": "国語", "part": "kokugo", "filter": "文学的文章", "name": "文学的文章の読解", "reading": true, "factcheck": false, "n": 9}, {"subject": "理科", "part": "rika", "filter": "光と音", "name": "光・音", "reading": false, "factcheck": true, "n": 10}, {"subject": "理科", "part": "rika", "filter": "力と圧力", "name": "力・圧力", "reading": false, "factcheck": true, "n": 10}, {"subject": "理科", "part": "rika", "filter": "電流と回路", "name": "電流と回路", "reading": false, "factcheck": true, "n": 10}, {"subject": "理科", "part": "rika", "filter": "電流と磁界", "name": "電流と磁界", "reading": false, "factcheck": true, "n": 10}, {"subject": "理科", "part": "rika", "filter": "運動とエネルギー", "name": "運動とエネルギー", "reading": false, "factcheck": true, "n": 10}, {"subject": "理科", "part": "rika", "filter": "物質と状態変化", "name": "物質の性質・状態変化", "reading": false, "factcheck": true, "n": 10}, {"subject": "理科", "part": "rika", "filter": "化学変化と原子", "name": "化学変化と原子・分子", "reading": false, "factcheck": true, "n": 10}, {"subject": "理科", "part": "rika", "filter": "イオンと酸", "name": "イオン・酸とアルカリ", "reading": false, "factcheck": true, "n": 10}, {"subject": "理科", "part": "rika", "filter": "植物", "name": "植物のつくりとはたらき", "reading": false, "factcheck": true, "n": 10}, {"subject": "理科", "part": "rika", "filter": "動物と人体", "name": "動物・人体", "reading": false, "factcheck": true, "n": 10}, {"subject": "理科", "part": "rika", "filter": "生殖と遺伝", "name": "生殖・遺伝", "reading": false, "factcheck": true, "n": 10}, {"subject": "理科", "part": "rika", "filter": "大地の変化", "name": "大地の変化（地層・火山・地震）", "reading": false, "factcheck": true, "n": 10}, {"subject": "理科", "part": "rika", "filter": "天気", "name": "天気とその変化", "reading": false, "factcheck": true, "n": 10}, {"subject": "理科", "part": "rika", "filter": "天体", "name": "地球と宇宙（天体）", "reading": false, "factcheck": true, "n": 10}, {"subject": "社会", "part": "shakai", "filter": "世界地理", "name": "世界地理", "reading": false, "factcheck": true, "n": 10}, {"subject": "社会", "part": "shakai", "filter": "日本地理", "name": "日本地理", "reading": false, "factcheck": true, "n": 10}, {"subject": "社会", "part": "shakai", "filter": "歴史 古代", "name": "歴史 古代〜平安", "reading": false, "factcheck": true, "n": 10}, {"subject": "社会", "part": "shakai", "filter": "歴史 中世", "name": "歴史 鎌倉〜室町", "reading": false, "factcheck": true, "n": 10}, {"subject": "社会", "part": "shakai", "filter": "歴史 近世", "name": "歴史 安土桃山〜江戸", "reading": false, "factcheck": true, "n": 10}, {"subject": "社会", "part": "shakai", "filter": "歴史 近代", "name": "歴史 明治〜大正", "reading": false, "factcheck": true, "n": 10}, {"subject": "社会", "part": "shakai", "filter": "歴史 現代", "name": "歴史 昭和〜現代", "reading": false, "factcheck": true, "n": 10}, {"subject": "社会", "part": "shakai", "filter": "公民 政治", "name": "公民 政治（憲法・人権・三権）", "reading": false, "factcheck": true, "n": 10}, {"subject": "社会", "part": "shakai", "filter": "公民 経済", "name": "公民 経済", "reading": false, "factcheck": true, "n": 10}, {"subject": "社会", "part": "shakai", "filter": "公民 国際", "name": "公民 国際社会", "reading": false, "factcheck": true, "n": 10}, {"subject": "社会", "part": "shakai", "filter": "資料読み取り", "name": "資料・統計の読み取り", "reading": false, "factcheck": true, "n": 10}]
const VDIR = 'scripts/chugaku_dojo/verified'

const AUTHOR_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['questions'],
  properties: {
    questions: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        required: ['stem', 'passage', 'choices', 'answer_index', 'unit', 'explanation'],
        properties: {
          stem: { type: 'string' },
          passage: { type: 'string' },
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
  type: 'object', additionalProperties: false,
  required: ['answers'],
  properties: {
    answers: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        required: ['i', 'choice_index'],
        properties: { i: { type: 'integer' }, choice_index: { type: 'integer', minimum: 0, maximum: 3 } },
      },
    },
  },
}

const AUDIT_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['verdicts'],
  properties: {
    verdicts: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        required: ['i', 'factually_correct', 'issue'],
        properties: {
          i: { type: 'integer' },
          factually_correct: { type: 'boolean' },
          issue: { type: 'string' },
        },
      },
    },
  },
}

const PERSIST_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['ok', 'bytes'],
  properties: { ok: { type: 'boolean' }, bytes: { type: 'integer' }, note: { type: 'string' } },
}

function authorPrompt(u) {
  const readingBlock = u.reading ? `
【読解単元の特別指示】この単元「${u.filter}」は本文付き読解です。
- ${u.subject === '英語'
    ? '英文パッセージ(80〜120語・中学卒業〜公立高校入試の語彙/文法)を3本作り、各パッセージに設問3問(内容一致/指示語/語句/要旨)。'
    : '日本語の本文(説明的or文学的・300〜450字・中学生向け・著作権フリーの完全オリジナル)を3本作り、各本文に設問3問(要旨/指示語/心情/語句)。'}
- 各設問の "passage" フィールドに、その設問が属する本文の全文を入れる(同じ本文の3問は同一 passage 文字列)。
- 本文だけで解ける自己完結。stem は本文への参照(「本文の内容として正しいものは」等)。` : `
- "passage" は空文字 "" にする(本文不要の知識/技能問題)。stem 単体+選択肢で完全に解ける自己完結問題。`

  const subjectHint = ({
    '数学': '計算・数値は厳密に正しく。図が必須になる問題は避け、必要な条件は全て文章で与える。答えの数値/式は一意。explanation に途中式(値のみ)を書く。',
    '英語': '公立高校入試標準の語彙・文法。文法選択/適語補充/語形変化/並べ替えの正答/対話応答/語法。英文は自然でネイティブが認める1択のみ正解。',
    '国語': '漢字・語句・文法(品詞/活用/識別)・敬語・古文入門(歴史的仮名遣い/係り結び/基礎古語)・詩歌(表現技法/季語/形式)。中学履修範囲のみ。正答は一意。',
    '理科': '中学理科の教科書事実のみ(公立入試頻出)。用語・法則・数値・実験結果は正確に。曖昧/高校範囲/諸説ある事項は出さない。',
    '社会': '中学社会の教科書事実のみ(公立入試頻出)。年号・人名・制度・地名・統計は正確に。曖昧/諸説ある/細かすぎる事項は出さない。',
  })[u.subject] || ''

  return `あなたは中学校の定期テスト・公立高校入試の作問のプロです。教科「${u.subject}」・単元「${u.name}」(弱点克服キー「${u.filter}」)の4択問題を、公立高校入試 標準レベル(中1〜中3の履修範囲)でちょうど ${u.n} 問つくってください。

【厳守ルール】
1. 各問は4択・正解はちょうど1つ・誰が見ても一意に決まる(2正解・0正解・曖昧を禁止)。
2. "answer_index" は正解選択肢の0始まりindex(0〜3)。作問時点の並び順で正しく指定。
3. "unit" フィールドは必ず厳密に "${u.filter}" という文字列にする(他の語を足さない)。
4. "explanation" は必ず 【単元】${u.filter}。正解は「<正解選択肢の文字列そのまま>」。 で始め、続けて中学生にわかる短い解説(1〜3文)。
   ★explanation では正解を「文字列(値)」でのみ示す。選択肢の位置(ア/A/①/1番目/上から2つ目 等)を絶対に書かない(後で位置をシャッフルするため)。
5. 誤答選択肢は「中学生がやりがちな典型的な間違い」にする(荒唐無稽な選択肢を入れない)。
6. ${subjectHint}
7. 単元全体を偏りなくカバーし、基本〜標準〜やや応用を混ぜる。同じ問いの焼き直しを避ける。
${readingBlock}

出力は指定スキーマの JSON のみ。`
}

function solvePrompt(u, blind, k) {
  const persona = [
    'あなたは中学範囲を丁寧に解く受験生です。各設問を落ち着いて解き、最も正しい選択肢を1つ選んでください。',
    'あなたは「2つ目の正解候補・曖昧さ」を探す批判的採点者です。各設問について最も擁護できる唯一解を選び、迷う場合も自分の最善解を出してください。',
    'あなたは各選択肢と設問文の事実/論理の誤りを点検する校閲者です。キー(出題者想定解)に引きずられず、独立に最も正しい選択肢を選んでください。',
  ][k]
  return `${persona}
教科「${u.subject}」単元「${u.name}」の4択問題を独立に解答します。正解や解説は与えられていません。各設問の "choices" から最も正しい選択肢の0始まりindexを選び、answers 配列で返してください(iは設問番号)。

問題(JSON):
${JSON.stringify(blind, null, 1)}

出力は指定スキーマの JSON のみ。`
}

function auditPrompt(u, auditQs) {
  return `あなたは中学「${u.subject}」の事実検証者です。単元「${u.name}」の各問について、出題者が正解としている選択肢(answer)と設問文の事実が、中学教科書レベルで正しいか検証してください。年号・人名・制度・地名・数値・法則・用語・実験結果などに誤りがないか厳密に確認します。少しでも不確かなら WebSearch(必要ならToolSearchで有効化)で裏取りしてください。

判定: 正解キーと設問の事実に誤りが無ければ factually_correct=true。誤り(誤った年号/人名/法則/数値、または正解キー自体が誤り)があれば false にし、issue に理由を短く記す。

問題(JSON):
${JSON.stringify(auditQs, null, 1)}

出力は指定スキーマの JSON のみ。`
}

function persistPrompt(path, arr) {
  return `Write ツールを使って、次の JSON 配列を "${path}" に一字一句そのまま(整形・加筆・省略なし)書き込んでください。書き込み後、書き込んだバイト数を報告してください。

内容:
${JSON.stringify(arr, null, 1)}

出力は指定スキーマの JSON のみ(ok, bytes)。`
}

let idxByPart = {}
const summary = await pipeline(
  UNITS,
  // stage 1: author
  async (u) => {
    const out = await agent(authorPrompt(u), { label: `author:${u.subject}/${u.filter}`, phase: 'Author', schema: AUTHOR_SCHEMA })
    const qs = (out && Array.isArray(out.questions)) ? out.questions : []
    return { u, questions: qs }
  },
  // stage 2: 3 independent blind solvers (+ audit for 社会/理科), filter to unanimous survivors
  async (prev, u0, idx) => {
    const { u, questions } = prev
    if (!questions.length) return { u, kept: [], authored: 0, note: 'author empty' }
    const blind = questions.map((q, i) => ({ i, passage: q.passage || '', stem: q.stem, choices: q.choices }))
    const solvers = await parallel([0, 1, 2].map(k => () =>
      agent(solvePrompt(u, blind, k), { label: `solve${k + 1}:${u.filter}`, phase: 'Verify', schema: SOLVE_SCHEMA })
    ))
    const votes = solvers.filter(Boolean).map(s => {
      const m = {}; (s.answers || []).forEach(a => { m[a.i] = a.choice_index }); return m
    })
    // require >=3 solvers present and ALL agree with author's answer_index (skill: 3独立盲ソルバー全員一致)
    let kept = questions
      .map((q, i) => ({ q, i }))
      .filter(({ q, i }) => votes.length >= 3 && votes.every(v => v[i] === q.answer_index))
    let auditDropped = 0
    if (u.factcheck && kept.length) {
      const auditQs = kept.map(({ q, i }) => ({ i, stem: q.stem, choices: q.choices, answer: q.choices[q.answer_index], explanation: q.explanation }))
      const audit = await agent(auditPrompt(u, auditQs), { label: `audit:${u.filter}`, phase: 'Verify', schema: AUDIT_SCHEMA, agentType: 'general-purpose', effort: 'high' })
      const bad = new Set(((audit && audit.verdicts) || []).filter(v => !v.factually_correct).map(v => v.i))
      auditDropped = kept.filter(({ i }) => bad.has(i)).length
      kept = kept.filter(({ i }) => !bad.has(i))
    }
    return { u, kept: kept.map(({ q }) => q), authored: questions.length, unanimous: kept.length + auditDropped, auditDropped }
  },
  // stage 3: persist survivors to disk (subagent uses Write)
  async (prev, u0, idx) => {
    const { u, kept, authored, unanimous, auditDropped } = prev
    if (!kept || !kept.length) return { subject: u.subject, part: u.part, filter: u.filter, authored: authored || 0, kept: 0, unanimous: unanimous || 0, auditDropped: auditDropped || 0, path: null }
    const path = `${VDIR}/${u.part}__${idx}.json`
    const payload = kept.map(q => ({
      subject: u.subject, part: u.part, filter: u.filter, unit: u.filter,
      stem: q.stem, passage: q.passage || '', choices: q.choices, answer_index: q.answer_index,
      explanation: q.explanation,
    }))
    const res = await agent(persistPrompt(path, payload), { label: `persist:${u.filter}`, phase: 'Persist', schema: PERSIST_SCHEMA })
    return { subject: u.subject, part: u.part, filter: u.filter, authored: authored || 0, kept: kept.length, unanimous: unanimous || 0, auditDropped: auditDropped || 0, path, persisted: !!(res && res.ok) }
  }
)

const flat = summary.filter(Boolean)
const bySubject = {}
for (const r of flat) {
  const s = (bySubject[r.subject] = bySubject[r.subject] || { authored: 0, kept: 0, auditDropped: 0, units: 0 })
  s.authored += r.authored; s.kept += r.kept; s.auditDropped += r.auditDropped; s.units += 1
}
log(`DONE units=${flat.length} kept=${flat.reduce((a, r) => a + r.kept, 0)} authored=${flat.reduce((a, r) => a + r.authored, 0)}`)
return { bySubject, totalKept: flat.reduce((a, r) => a + r.kept, 0), totalAuthored: flat.reduce((a, r) => a + r.authored, 0), units: flat.map(r => ({ part: r.part, filter: r.filter, authored: r.authored, kept: r.kept, auditDropped: r.auditDropped, persisted: r.persisted, path: r.path })) }
