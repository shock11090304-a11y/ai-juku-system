export const meta = {
  name: 'kaki-eng-verify',
  description: '夏期講習 英語 全20セッションを独立ブラインド採点＋品質クリティックで検証',
  phases: [
    { title: 'Solve', detail: '各セッションを解答を伏せて独立に解く' },
    { title: 'Critique', detail: '各セッションの英語品質・正解妥当性・曖昧性を敵対的に検査' },
  ],
}

const ROOT = '/Users/adachishouhei/ai-juku-system/scripts/kaki_koushuu_eng'

const KEYS = []
for (const lv of ['chu', 'kou']) for (const t of ['g', 'r']) for (let i = 1; i <= 5; i++) KEYS.push(`${lv}_${t}${i}`)

phase('Solve')
log(`全${KEYS.length}セッションを 独立ソルバー＋クリティック で検証`)

const results = await parallel(KEYS.map(key => async () => {
  // --- 1) 独立ブラインド採点 ---
  const blindPath = `${ROOT}/blind/${key}.json`
  const verifyPath = `${ROOT}/verify/${key}.json`
  const solvePrompt =
`あなたは英語の熟練解答者。解答が伏せられた問題ファイルを読み、あなた自身の力だけで各設問を解く（元の正解は見えない）。

対象ファイル（読み込む）: ${blindPath}
内容は {"key","kind","items":[...], (長文なら)"passage"} 形式。items の各要素は "id" と "type" を持つ。

各 id について、あなたの解答を次の形式で決める:
- "mc" / "rc_mc": 選んだ選択肢の 0 起点インデックス（整数）
- "error": 誤りを含む下線の記号（"a"/"b"/"c"/"d" の文字列）
- "fill": 空所に入る英語の語句（文字列）
- "order": tokens を並べ替えた完成文（文字列・末尾ピリオド無し）
- "rewrite": 各空所に入る語の配列（例 ["too","to"]）

【作業】
1) じっくり解く（長文は passage を精読）。推測でなく根拠を持って。
2) Write で次に保存（JSONのみ）: ${verifyPath}
   形式: {"key":"${key}","answers":{"<id>":<解答>, ...}}
3) 返答は1行のみ: 「solve ${key}: N items answered」`
  const solveOut = await agent(solvePrompt, { label: `solve:${key}`, phase: 'Solve' })

  // --- 2) 品質クリティック（正解を見た上で敵対的検査） ---
  const dataPath = `${ROOT}/data/${key}.json`
  const critPath = `${ROOT}/critique/${key}.json`
  const critPrompt =
`あなたは大手予備校の英語科・校閲責任者。教材1セッションの完成データ（正解・解説つき）を敵対的に検査する。

対象ファイル（読み込む）: ${dataPath}

【チェック観点】
A) 英文の自然さ・文法的正しさ（不自然な英語・非文・スペル/冠詞/語法ミス）— 例文・問題文・選択肢・（長文なら）本文すべて。
B) 正解の妥当性: 各設問の "ans"/"correct"/"blanks"/"models" が本当に正しいか。誤答（distractor）に「実は正解になりうるもの」が無いか。
C) 曖昧性: 正解が一義に定まるか（複数正解・正解無しになっていないか）。
D) order は tokens を並べ替えて ans に一致するか。rewrite は空所数と blanks 数が合うか。fill は文脈上その語で確定するか。
E) 解説(exp)が論点を正しく説明しているか（誤った理由付けが無いか）。
F) 長文の場合: 本文が指定レベル・語数に合うか、trans（全訳）が本文と一致するか、設問が本文だけで解けるか、事実誤りが無いか。
G) レベル整合: ${key.startsWith('chu') ? '中学生（中3・高校受験）に難しすぎ/易しすぎないか' : '高校（大学受験）として妥当な難度か'}。

【出力】問題があるものだけを issues に挙げる（無ければ空配列）。
1) Write で保存（JSONのみ）: ${critPath}
   形式: {"key":"${key}","issues":[{"id":"<tier+番号 or q番号 or passage/general>","severity":"high|med|low","problem":"<何が問題か>","fix":"<推奨修正>"}]}
   ※ high=正解が誤り/非文/事実誤り、med=曖昧・distractor弱い・解説の誤り、low=語法の好みレベル。
2) 返答は1行のみ: 「crit ${key}: H<high数> M<med数> L<low数>」`
  const critOut = await agent(critPrompt, { label: `crit:${key}`, phase: 'Critique' })

  return { key, solve: (solveOut || '').slice(-120), crit: (critOut || '').slice(-120) }
}))

return { total: KEYS.length, results: results.filter(Boolean) }
