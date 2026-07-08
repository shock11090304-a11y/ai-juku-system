export const meta = {
  name: 'chugaku-math-review',
  description: '追加した中学数学211問を独立第2ゲートで敵対検証: 数値Python再計算+曖昧/自己完結点検→フラグをレフェリーが再解答で裁定→DROP対象indexを返す。',
  phases: [
    { title: 'Critique', detail: '各単元を2独立クリティック(数値再計算+敵対曖昧点検)' },
    { title: 'Referee', detail: 'フラグ付き設問のみ独立レフェリーが裁定' },
  ],
}

const TARGETS = [
  { gi: 13, filter: '正負の数' }, { gi: 14, filter: '式の計算' }, { gi: 15, filter: '一次方程式' },
  { gi: 16, filter: '連立方程式' }, { gi: 17, filter: '平方根' }, { gi: 18, filter: '二次方程式' },
  { gi: 19, filter: '比例・反比例' }, { gi: 20, filter: '一次関数' }, { gi: 21, filter: '二乗に比例' },
  { gi: 22, filter: '合同と証明' }, { gi: 23, filter: '相似' }, { gi: 24, filter: '円周角' },
  { gi: 25, filter: '三平方の定理' }, { gi: 26, filter: '確率' }, { gi: 27, filter: 'データの活用' },
].map((t) => ({ ...t, path: `scripts/chugaku_dojo/add/math__${t.gi}.json` }))
const _rargs = typeof args === 'string' && args.trim() ? JSON.parse(args) : args
const REVIEW_TARGETS = (Array.isArray(_rargs) && _rargs.length) ? TARGETS.filter((t) => _rargs.includes(t.gi)) : TARGETS

const VERDICT_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['verdicts'],
  properties: {
    verdicts: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false, required: ['i', 'ok', 'issue', 'detail'],
        properties: {
          i: { type: 'integer' },
          ok: { type: 'boolean' },
          issue: { type: 'string' },     // ok=true のときは "none"
          detail: { type: 'string' },    // 自分が計算した正答・問題点
        },
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

function numericPrompt(t) {
  return `あなたは中学数学の非常に厳格な検算者です。ファイル ${t.path} を Read ツールで読んでください(JSON配列。各要素は {stem, choices[4], answer_index, explanation})。
配列の各要素 i(0始まり)について、あなた自身で最初から解き直し、必要な計算・場合の数の全列挙・方程式の求解は必ず Bash ツールで python3 を実行して地上真値を出してください(暗算に頼らない)。
そのうえで次を全て満たすときだけ ok=true:
 (1) choices[answer_index] が唯一の正解である。
 (2) 4つの choices がすべて異なる。
 (3) explanation の「正解は「…」」に書かれた値が choices[answer_index] と完全一致する。
 (4) explanation 本文の計算が正しい。
一つでも崩れたら ok=false。issue は wrong_key / not_unique / dup_choice / expl_mismatch / expl_calc_wrong / other のいずれか、detail に「自分がpythonで出した正答」と根拠を書く。
verdicts[{i, ok, issue, detail}] を全要素分返す。出力は指定スキーマJSONのみ。`
}

function adversarialPrompt(t) {
  return `あなたは中学数学の作問を"壊す"敵対的レビュアーです。ファイル ${t.path} を Read ツールで読んでください(JSON配列 {stem, choices[4], answer_index, explanation})。
配列の各要素 i(0始まり)について、次の穴を探してください:
 (a) answer_index 以外にも「正解といえてしまう選択肢」がないか(2正解・曖昧)。
 (b) 図・グラフが無いと解けない、条件が不足している等で一意に解けないものはないか(自己完結でない)。
 (c) 単元「${t.filter}」の範囲外・別単元の問題になっていないか。
 (d) stem/choices/explanation に、数値や式の誤植で意味が変わる箇所がないか。
問題があれば ok=false(issue=not_unique / needs_figure / underspecified / out_of_unit / typo / other、detail に具体箇所)。問題なければ ok=true。
必要なら Bash で python3 を使って裏取りしてよい。verdicts[{i, ok, issue, detail}] を全要素分返す。出力は指定スキーマJSONのみ。`
}

function refereePrompt(t, flagged) {
  return `あなたは中立の主席検証者(レフェリー)です。ファイル ${t.path} を Read ツールで読み、下記の"フラグ付き"設問だけを独立に精査してください。
フラグ(他の検証者の指摘): ${JSON.stringify(flagged)}
各 i について、あなた自身で最初から解き直し(数値は Bash の python3 で計算)、指摘が本当に正しいか裁定してください。
 - 本当に誤り(誤キー/2正解/曖昧/要図/誤植/解説不整合など)が存在する → drop=true。
 - 指摘が誤りで設問は正しく一意に解ける → drop=false。
reason に、自分が出した正答と裁定理由を簡潔に書く。rulings[{i, drop, reason}] を返す。出力は指定スキーマJSONのみ。`
}

const results = await pipeline(
  REVIEW_TARGETS,
  // Phase 1: 2独立クリティック
  async (t) => {
    const [num, adv] = await parallel([
      () => agent(numericPrompt(t), { label: `num:${t.filter}`, phase: 'Critique', schema: VERDICT_SCHEMA, agentType: 'general-purpose', effort: 'high' }),
      () => agent(adversarialPrompt(t), { label: `adv:${t.filter}`, phase: 'Critique', schema: VERDICT_SCHEMA, agentType: 'general-purpose', effort: 'high' }),
    ])
    const byI = new Map()
    for (const v of [...(num?.verdicts || []), ...(adv?.verdicts || [])]) {
      if (!v.ok) {
        const cur = byI.get(v.i) || []
        cur.push({ issue: v.issue, detail: v.detail })
        byI.set(v.i, cur)
      }
    }
    const flagged = [...byI.entries()].map(([i, issues]) => ({ i, issues }))
    return { t, flagged, numOk: !!num, advOk: !!adv }
  },
  // Phase 2: フラグ付きのみレフェリー裁定
  async (prev) => {
    const { t, flagged } = prev
    if (!flagged.length) {
      log(`${t.filter}: フラグ0 → 全採用`)
      return { gi: t.gi, filter: t.filter, drop: [], flaggedCount: 0 }
    }
    const ref = await agent(refereePrompt(t, flagged), {
      label: `ref:${t.filter}`, phase: 'Referee', schema: REF_SCHEMA, agentType: 'general-purpose', effort: 'high',
    })
    const rulings = ref?.rulings || []
    const drop = rulings.filter((r) => r.drop).map((r) => ({ i: r.i, reason: r.reason }))
    // レフェリーが応答しなかった i は安全側で drop
    const ruledSet = new Set(rulings.map((r) => r.i))
    for (const f of flagged) {
      if (!ruledSet.has(f.i)) drop.push({ i: f.i, reason: 'referee無応答→安全側drop', issues: f.issues })
    }
    log(`${t.filter}: フラグ${flagged.length} → DROP ${drop.length}`)
    return { gi: t.gi, filter: t.filter, drop, flaggedCount: flagged.length }
  }
)

const flat = results.filter(Boolean)
const totalDrop = flat.reduce((a, r) => a + (r.drop ? r.drop.length : 0), 0)
const totalFlag = flat.reduce((a, r) => a + (r.flaggedCount || 0), 0)
log(`REVIEW DONE flagged=${totalFlag} confirmedDrop=${totalDrop}`)
return { units: flat, totalFlag, totalDrop }
