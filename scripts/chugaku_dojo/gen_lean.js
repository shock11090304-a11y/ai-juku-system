export const meta = {
  name: 'chugaku-dojo-gen-lean',
  description: '中学生 弱点克服ドリル(残り27単元)を lean 2段(作問→独立レビュー兼保存)で生成。レート制限を避けるため agent 数を半減。',
  phases: [
    { title: 'Author', detail: '残単元を作問(自己完結4択)' },
    { title: 'Review+Persist', detail: '独立再解答+社会理科は事実確認→合格のみ verified/ へ保存' },
  ],
}

const VDIR = 'scripts/chugaku_dojo/verified'
const UNITS = [{"subject": "英語", "part": "eng", "filter": "be動詞・一般動詞", "name": "be動詞・一般動詞", "reading": false, "factcheck": false, "n": 10, "gi": 0}, {"subject": "英語", "part": "eng", "filter": "時制", "name": "時制（過去・進行・未来）", "reading": false, "factcheck": false, "n": 10, "gi": 1}, {"subject": "英語", "part": "eng", "filter": "助動詞", "name": "助動詞", "reading": false, "factcheck": false, "n": 10, "gi": 2}, {"subject": "英語", "part": "eng", "filter": "名詞・代名詞・冠詞", "name": "名詞・代名詞・冠詞", "reading": false, "factcheck": false, "n": 10, "gi": 3}, {"subject": "英語", "part": "eng", "filter": "比較", "name": "比較", "reading": false, "factcheck": false, "n": 10, "gi": 4}, {"subject": "英語", "part": "eng", "filter": "不定詞・動名詞", "name": "不定詞・動名詞", "reading": false, "factcheck": false, "n": 10, "gi": 5}, {"subject": "英語", "part": "eng", "filter": "分詞", "name": "分詞（現在分詞・過去分詞）", "reading": false, "factcheck": false, "n": 10, "gi": 6}, {"subject": "英語", "part": "eng", "filter": "受動態", "name": "受動態", "reading": false, "factcheck": false, "n": 10, "gi": 7}, {"subject": "英語", "part": "eng", "filter": "現在完了", "name": "現在完了", "reading": false, "factcheck": false, "n": 10, "gi": 8}, {"subject": "英語", "part": "eng", "filter": "関係代名詞", "name": "関係代名詞", "reading": false, "factcheck": false, "n": 10, "gi": 9}, {"subject": "英語", "part": "eng", "filter": "接続詞・前置詞", "name": "接続詞・前置詞", "reading": false, "factcheck": false, "n": 10, "gi": 10}, {"subject": "英語", "part": "eng", "filter": "会話表現", "name": "会話・熟語表現", "reading": false, "factcheck": false, "n": 10, "gi": 11}, {"subject": "数学", "part": "math", "filter": "正負の数", "name": "正負の数・四則計算", "reading": false, "factcheck": false, "n": 10, "gi": 13}, {"subject": "数学", "part": "math", "filter": "式の計算", "name": "文字式・式の計算", "reading": false, "factcheck": false, "n": 10, "gi": 14}, {"subject": "理科", "part": "rika", "filter": "生殖と遺伝", "name": "生殖・遺伝", "reading": false, "factcheck": true, "n": 10, "gi": 46}, {"subject": "理科", "part": "rika", "filter": "天気", "name": "天気とその変化", "reading": false, "factcheck": true, "n": 10, "gi": 48}, {"subject": "社会", "part": "shakai", "filter": "世界地理", "name": "世界地理", "reading": false, "factcheck": true, "n": 10, "gi": 50}, {"subject": "社会", "part": "shakai", "filter": "日本地理", "name": "日本地理", "reading": false, "factcheck": true, "n": 10, "gi": 51}, {"subject": "社会", "part": "shakai", "filter": "歴史 古代", "name": "歴史 古代〜平安", "reading": false, "factcheck": true, "n": 10, "gi": 52}, {"subject": "社会", "part": "shakai", "filter": "歴史 中世", "name": "歴史 鎌倉〜室町", "reading": false, "factcheck": true, "n": 10, "gi": 53}, {"subject": "社会", "part": "shakai", "filter": "歴史 近世", "name": "歴史 安土桃山〜江戸", "reading": false, "factcheck": true, "n": 10, "gi": 54}, {"subject": "社会", "part": "shakai", "filter": "歴史 近代", "name": "歴史 明治〜大正", "reading": false, "factcheck": true, "n": 10, "gi": 55}, {"subject": "社会", "part": "shakai", "filter": "歴史 現代", "name": "歴史 昭和〜現代", "reading": false, "factcheck": true, "n": 10, "gi": 56}, {"subject": "社会", "part": "shakai", "filter": "公民 政治", "name": "公民 政治（憲法・人権・三権）", "reading": false, "factcheck": true, "n": 10, "gi": 57}, {"subject": "社会", "part": "shakai", "filter": "公民 経済", "name": "公民 経済", "reading": false, "factcheck": true, "n": 10, "gi": 58}, {"subject": "社会", "part": "shakai", "filter": "公民 国際", "name": "公民 国際社会", "reading": false, "factcheck": true, "n": 10, "gi": 59}, {"subject": "社会", "part": "shakai", "filter": "資料読み取り", "name": "資料・統計の読み取り", "reading": false, "factcheck": true, "n": 10, "gi": 60}]

const AUTHOR_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['questions'],
  properties: {
    questions: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        required: ['stem', 'passage', 'choices', 'answer_index', 'unit', 'explanation'],
        properties: {
          stem: { type: 'string' }, passage: { type: 'string' },
          choices: { type: 'array', items: { type: 'string' }, minItems: 4, maxItems: 4 },
          answer_index: { type: 'integer', minimum: 0, maximum: 3 },
          unit: { type: 'string' }, explanation: { type: 'string' },
        },
      },
    },
  },
}
const REVIEW_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['ok', 'kept', 'dropped'],
  properties: { ok: { type: 'boolean' }, kept: { type: 'integer' }, dropped: { type: 'integer' }, note: { type: 'string' } },
}

function authorPrompt(u) {
  const subjectHint = ({
    '数学': '計算・数値は厳密に。図必須の問題は避け条件は全て文章で。答えは一意。explanationに途中式(値のみ)。',
    '英語': '公立高校入試標準の文法/適語補充/語形変化/対話応答/語法。ネイティブが認める1択のみ正解。',
    '理科': '中学理科の教科書事実のみ。用語・法則・数値・実験結果を正確に。高校範囲/諸説ある事項は出さない。',
    '社会': '中学社会の教科書事実のみ(公立入試頻出)。年号・人名・制度・地名・統計を正確に。諸説ある/細かすぎる事項は避ける。',
  })[u.subject] || ''
  return `あなたは中学校の定期テスト・公立高校入試の作問のプロです。教科「${u.subject}」・単元「${u.name}」(弱点キー「${u.filter}」)の4択問題を、公立高校入試 標準レベル(中1〜中3)でちょうど ${u.n} 問つくってください。

【厳守】
1. 4択・正解ちょうど1つ・一意(2正解/0正解/曖昧禁止)。
2. answer_index=正解の0始まりindex。
3. unit フィールドは厳密に "${u.filter}"。
4. explanation は 【単元】${u.filter}。正解は「<正解選択肢の文字列>」。 で始め、中学生向けの短い解説(1〜3文)。正解は必ず「文字列(値)」で示し、位置(ア/A/①/N番目)を書かない。
5. 誤答は中学生がやりがちな典型ミス。荒唐無稽な選択肢禁止。
6. ${subjectHint}
7. 単元全体を偏りなくカバー・基本〜標準〜やや応用を混ぜる。
8. passage は "" (本文不要の自己完結問題)。
出力は指定スキーマJSONのみ。`
}

function reviewPrompt(u, questions, path) {
  const fc = u.factcheck ? `\n【事実確認(社会/理科)】各問の正解キーと設問文の事実(年号/人名/制度/地名/数値/法則/実験結果)を中学教科書レベルで検証。少しでも不確かなら WebSearch(必要ならToolSearchで有効化)で裏取り。事実誤り or キー誤りは drop。` : ''
  return `あなたは中学「${u.subject}」の独立検証者です。以下の4択問題(作問者の想定解 answer_index 付き)を、あなた自身で1問ずつ「先に自力で解いてから」想定解と照合してください。
- あなたの独立解答が answer_index と一致し、かつ選択肢が4つとも異なり、正解が一意である問題だけを「合格」とする。
- あなたの解答が違う/曖昧/2正解/選択肢重複 の問題は drop。${fc}

合格した問題だけを、次の JSON 配列として Write ツールで "${path}" に保存してください(1問=1オブジェクト、値は作問者のものをそのまま・drop した問題は含めない):
  [{"subject":"${u.subject}","part":"${u.part}","filter":"${u.filter}","unit":"${u.filter}","stem":..., "passage":"", "choices":[...4...], "answer_index":0-3, "explanation":...}, ...]
choices の順序と answer_index の対応を絶対に崩さないこと。保存後、kept(合格数)/dropped(除外数) を報告。

検証対象(JSON):
${JSON.stringify(questions, null, 1)}

出力は指定スキーマJSONのみ(ok,kept,dropped)。`
}

const results = await pipeline(
  UNITS,
  async (u) => {
    const out = await agent(authorPrompt(u), { label: `author:${u.part}/${u.filter}`, phase: 'Author', schema: AUTHOR_SCHEMA })
    return { u, questions: (out && Array.isArray(out.questions)) ? out.questions : [] }
  },
  async (prev) => {
    const { u, questions } = prev
    if (!questions.length) return { part: u.part, filter: u.filter, gi: u.gi, kept: 0, note: 'author empty', path: null }
    const path = `${VDIR}/${u.part}__${u.gi}.json`
    const res = await agent(reviewPrompt(u, questions, path), {
      label: `review:${u.part}/${u.filter}`, phase: 'Review+Persist', schema: REVIEW_SCHEMA,
      agentType: 'general-purpose', effort: u.factcheck ? 'high' : 'medium',
    })
    return { part: u.part, filter: u.filter, gi: u.gi, authored: questions.length, kept: (res && res.kept) || 0, dropped: (res && res.dropped) || 0, path, ok: !!(res && res.ok) }
  }
)

const flat = results.filter(Boolean)
log(`LEAN DONE units=${flat.length} kept=${flat.reduce((a, r) => a + (r.kept || 0), 0)}`)
return { units: flat, totalKept: flat.reduce((a, r) => a + (r.kept || 0), 0), okCount: flat.filter(r => r.ok).length }
