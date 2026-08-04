export const meta = {
  name: 'chugaku-review-expand',
  description: '増量した中学ドリル(英/国/理/社)を独立第2ゲートで敵対検証: 正答/曖昧/自己完結点検+事実科目はWebSearch裏取り→フラグをレフェリーが裁定→DROP index返す。',
  phases: [
    { title: 'Critique', detail: '2独立クリティック(事実科目はWebSearch)' },
    { title: 'Referee', detail: 'フラグ付きのみレフェリー裁定' },
  ],
}

const A = typeof args === 'string' ? JSON.parse(args) : args
const PART = A.part, SUBJECT = A.subject
const TARGETS = A.units.map((u) => ({ ...u, path: `scripts/chugaku_dojo/add2/${PART}__${u.gi}.json` }))

const VERDICT_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['verdicts'],
  properties: {
    verdicts: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false, required: ['i', 'ok', 'issue', 'detail'],
        properties: { i: { type: 'integer' }, ok: { type: 'boolean' }, issue: { type: 'string' }, detail: { type: 'string' } },
      },
    },
  },
}
const REF_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['rulings'],
  properties: {
    rulings: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false, required: ['i', 'drop', 'reason'],
        properties: { i: { type: 'integer' }, drop: { type: 'boolean' }, reason: { type: 'string' } },
      },
    },
  },
}

function correctnessPrompt(t) {
  const fact = t.factcheck
    ? `各設問の正答キーと設問文の事実(年号/人名/制度/地名/数値/語義/法則/実験結果)を、少しでも不確かなら WebSearch(必要なら ToolSearch で有効化)で裏取りして検証する。中学教科書の定説と異なる/事実誤りは ok=false。`
    : `各設問を自分で最後まで解き、choices[answer_index] が唯一の正解であることを確認する。`
  return `あなたは中学「${SUBJECT}」の非常に厳格な検証者です。ファイル ${t.path} を Read ツールで読んでください(JSON配列 {stem, choices[4], answer_index, explanation, passage})。★passage(本文)が空でなければ読解問題です。必ず本文を読み、「本文だけを根拠に正解が一意か」を検証してください。
配列の各要素 i(0始まり)について次を確認し、全て満たすときだけ ok=true:
 (1) choices[answer_index] が唯一の正解。
 (2) 4つの choices がすべて異なり、正解と同値の選択肢が無い。
 (3) explanation の「正解は「…」」の値が choices[answer_index] と完全一致し、解説の内容(理由・年号・語義・計算)が正しい。
 (4) 図・本文なしで一意に解ける(自己完結)。
${fact}
一つでも崩れたら ok=false。issue は wrong_key / not_unique / dup_choice / expl_mismatch / expl_wrong / needs_context / fact_error / out_of_unit / other。detail に「正しいと考える答えと根拠(裏取りしたら出典も)」。verdicts[{i,ok,issue,detail}] を全要素分返す。出力は指定スキーマJSONのみ。`
}

function adversarialPrompt(t) {
  const fact = t.factcheck ? ' 事実(年号/人名/制度/語義等)は WebSearch で裏取りしてよい。' : ''
  return `あなたは中学「${SUBJECT}」の作問を"壊す"敵対的レビュアーです。ファイル ${t.path} を Read ツールで読んでください(JSON配列 {stem, choices[4], answer_index, explanation, passage})。★passage(本文)が空でなければ読解問題=本文も読んで検証する。
各要素 i(0始まり)について穴を探す:
 (a) answer_index 以外に「正解といえてしまう選択肢」が無いか(2正解・曖昧・正解と同義/同値)。
 (b) 図・本文・追加情報が無いと一意に解けない、条件不足はないか。
 (c) 単元「${t.filter}」の範囲外・別単元になっていないか。高校範囲に踏み込んでいないか。
 (d) stem/choices/explanation に、事実誤り・語形/数値の誤植・表記ゆれで意味が変わる箇所はないか。${fact}
問題があれば ok=false(issue=not_unique/needs_context/underspecified/out_of_unit/fact_error/typo/other、detail に具体箇所)。無ければ ok=true。verdicts[{i,ok,issue,detail}] を全要素分。出力は指定スキーマJSONのみ。`
}

function refereePrompt(t, flagged) {
  const fact = t.factcheck ? ' 事実は WebSearch で裏取りする。' : ''
  return `あなたは中立の主席検証者(レフェリー)です。ファイル ${t.path} を Read ツールで読み、下記フラグ付き設問だけを独立に精査してください。
フラグ(他検証者の指摘): ${JSON.stringify(flagged)}
各 i について自分で解き直し${fact}、指摘が本当に正しいか裁定する。本当に誤り(誤キー/2正解/曖昧/要文脈/事実誤り/範囲外/誤植/解説不整合)が存在するなら drop=true、指摘が誤りで設問は正しく一意に解けるなら drop=false。reason に自分の答えと根拠。rulings[{i,drop,reason}] を返す。出力は指定スキーマJSONのみ。`
}

const results = await pipeline(
  TARGETS,
  async (t) => {
    const [num, adv] = await parallel([
      () => agent(correctnessPrompt(t), { label: `chk:${PART}/${t.filter}`, phase: 'Critique', schema: VERDICT_SCHEMA, agentType: 'general-purpose', effort: 'high' }),
      () => agent(adversarialPrompt(t), { label: `adv:${PART}/${t.filter}`, phase: 'Critique', schema: VERDICT_SCHEMA, agentType: 'general-purpose', effort: 'high' }),
    ])
    const complete = !!num && !!adv   // どちらかの検証者が落ちたら未完了(rate-limit等)
    const byI = new Map()
    for (const v of [...(num?.verdicts || []), ...(adv?.verdicts || [])]) {
      if (!v.ok) { const c = byI.get(v.i) || []; c.push({ issue: v.issue, detail: v.detail }); byI.set(v.i, c) }
    }
    const flagged = [...byI.entries()].map(([i, issues]) => ({ i, issues }))
    return { t, flagged, complete }
  },
  async (prev) => {
    const { t, flagged, complete } = prev
    if (!complete) { log(`${PART}/${t.filter}: ⚠️検証者失敗=未完了(要再実行)`); return { gi: t.gi, filter: t.filter, drop: [], flaggedCount: 0, complete: false } }
    if (!flagged.length) { log(`${PART}/${t.filter}: フラグ0 → 全採用`); return { gi: t.gi, filter: t.filter, drop: [], flaggedCount: 0, complete: true } }
    const ref = await agent(refereePrompt(t, flagged), { label: `ref:${PART}/${t.filter}`, phase: 'Referee', schema: REF_SCHEMA, agentType: 'general-purpose', effort: 'high' })
    const rulings = ref?.rulings || []
    const drop = rulings.filter((r) => r.drop).map((r) => ({ i: r.i, reason: r.reason }))
    const ruled = new Set(rulings.map((r) => r.i))
    for (const f of flagged) if (!ruled.has(f.i)) drop.push({ i: f.i, reason: 'referee無応答→安全側drop' })
    log(`${PART}/${t.filter}: フラグ${flagged.length} → DROP ${drop.length}`)
    return { gi: t.gi, filter: t.filter, drop, flaggedCount: flagged.length, complete: true }
  }
)

const flat = results.filter(Boolean)
const incomplete = flat.filter((r) => !r.complete).map((r) => r.filter)
log(`REVIEW DONE ${PART} flagged=${flat.reduce((a, r) => a + (r.flaggedCount || 0), 0)} drop=${flat.reduce((a, r) => a + (r.drop ? r.drop.length : 0), 0)} incomplete=[${incomplete.join(',')}]`)
return { part: PART, units: flat, totalDrop: flat.reduce((a, r) => a + (r.drop ? r.drop.length : 0), 0), incomplete }
