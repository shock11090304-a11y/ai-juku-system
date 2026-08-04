export const meta = {
  name: 'kaki-eng-verify-grammar',
  description: '高難度化した文法10セッションを独立ブラインド採点＋品質クリティックで検証',
  phases: [{ title: 'Solve' }, { title: 'Critique' }],
}

const ROOT = '/Users/adachishouhei/ai-juku-system/scripts/kaki_koushuu_eng'
const KEYS = []
for (const lv of ['chu', 'kou']) for (let i = 1; i <= 5; i++) KEYS.push(`${lv}_g${i}`)

phase('Solve')
log(`高難度化した文法 全${KEYS.length}セッションを検証`)

const results = await parallel(KEYS.map(key => async () => {
  const blindPath = `${ROOT}/blind/${key}.json`
  const verifyPath = `${ROOT}/verify/${key}.json`
  const level = key.startsWith('kou') ? '大学受験（高校）' : '高校受験（中3）'
  const solvePrompt =
`あなたは英語の熟練解答者。解答が伏せられた文法問題を、自分の力だけで解く（元の正解は見えない）。難問が含まれるので慎重に。

読み込む: ${blindPath}  （{"items":[{id,type,...}]} 形式）
各 id の解答形式:
- "mc": 選んだ選択肢の 0 起点インデックス（整数）
- "error": 誤りを含む下線の記号（"a"/"b"/"c"/"d"）
- "fill": 空所に入る英語の語句（文字列）
- "order": tokens を並べ替えた完成文（文字列・末尾ピリオド無し）
- "rewrite": 各空所に入る語の配列（例 ["too","to"]）

Writeで保存: ${verifyPath}  形式 {"key":"${key}","answers":{"<id>":<解答>,...}}
返答は1行: 「solve ${key}: N items answered」`
  const solveOut = await agent(solvePrompt, { label: `solve:${key}`, phase: 'Solve' })

  const dataPath = `${ROOT}/data/${key}.json`
  const critPath = `${ROOT}/critique/${key}.json`
  const critPrompt =
`あなたは大手予備校の英語科・校閲責任者。高難度化した文法教材（正解・解説つき）を敵対的に検査する。レベル=${level}。

読み込む: ${dataPath}
【観点】A)英文の自然さ・文法的正しさ B)各設問の正解(ans/correct/blanks/models)が本当に正しいか、誤答に「実は正解になりうるもの」が無いか C)一義に定まるか（複数正解/正解無しが無いか）D)order は tokens並べ替えで ans に一致するか、rewrite は空所数と blanks数が一致するか、fill は文脈で確定するか E)解説(exp)の理由付けが正しいか F)難度整合: ${key.startsWith('kou') ? '標準はMARCH/関関同立・入試は早慶/旧帝レベルとして妥当か（易しすぎ/悪問でないか）' : '標準が難関私国立高レベルとして妥当か（中学範囲を超えていないか・悪問でないか）'}。

問題があるものだけ issues に。Writeで保存: ${critPath}  形式 {"key":"${key}","issues":[{"id","severity":"high|med|low","problem","fix"}]}
（high=正解が誤り/非文、med=曖昧・distractor弱い・解説誤り・範囲逸脱、low=好みレベル）
返答は1行: 「crit ${key}: H<n> M<n> L<n>」`
  const critOut = await agent(critPrompt, { label: `crit:${key}`, phase: 'Critique' })

  return { key, solve: (solveOut || '').slice(-100), crit: (critOut || '').slice(-100) }
}))

return { total: KEYS.length, results: results.filter(Boolean) }
