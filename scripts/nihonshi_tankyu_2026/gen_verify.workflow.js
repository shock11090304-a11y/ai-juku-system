export const meta = {
  name: 'nihonshi-tankyu-generate-verify',
  description: '共通テスト日本史探究の大問(組合せ/正誤/整序/疑問×考察)を作問→3盲ソルバー一致+3視点レビュー(史実正確性重視)→検証済みrowをJSONで返す',
  phases: [
    { title: 'Author', detail: '探究形式の大問を作問' },
    { title: 'Solve', detail: '3名が日本史知識で盲解答しキー一致を検証' },
    { title: 'Review', detail: '3視点(正答妥当/史実正確/自己完結・形式)で校閲' },
  ],
}

const SOURCE = 'kyotsu-nihonshi-tankyu-20260625'
const MODEL = 'claude-nihonshi-verified'

// 教科書頻出・確実な事実が多いテーマ(マニアック回避=史実リスク低)
const ITEMS = [
  // 古代
  { era:'古代', topic:'律令国家の成立(大化改新・大宝律令・二官八省・遣唐使・平城京遷都)' },
  { era:'古代', topic:'律令制下の土地制度と税(班田収授・公地公民・三世一身法・墾田永年私財法・初期荘園)' },
  { era:'古代', topic:'摂関政治の展開(藤原氏の他氏排斥・摂政関白・外戚政治・荘園の寄進)' },
  { era:'古代', topic:'院政と荘園(後三条天皇の荘園整理・白河院政・知行国・北面の武士・寄進地系荘園)' },
  // 中世
  { era:'中世', topic:'鎌倉幕府の成立と御家人制度(守護地頭・封建的主従関係・承久の乱・御成敗式目)' },
  { era:'中世', topic:'執権政治と蒙古襲来(北条氏の執権政治・元寇・徳政令・御家人の窮乏)' },
  { era:'中世', topic:'建武の新政と室町幕府(後醍醐天皇・南北朝の動乱・足利尊氏・守護大名・勘合貿易)' },
  { era:'中世', topic:'中世の社会経済(惣村・土一揆・座・定期市・応仁の乱と下剋上)' },
  // 近世
  { era:'近世', topic:'織豊政権と統一事業(楽市楽座・太閤検地・刀狩・兵農分離)' },
  { era:'近世', topic:'幕藩体制の確立(武家諸法度・参勤交代・幕府の職制・禁中並公家諸法度)' },
  { era:'近世', topic:'江戸幕府の三大改革(享保の改革・寛政の改革・天保の改革の内容と相違)' },
  { era:'近世', topic:'江戸の対外関係と田沼政治(いわゆる鎖国・四つの口・朝鮮通信使・田沼意次の重商政策)' },
  // 近代
  { era:'近代', topic:'明治維新と諸改革(廃藩置県・地租改正・徴兵令・殖産興業・文明開化)' },
  { era:'近代', topic:'自由民権運動と立憲体制(民撰議院設立建白書・国会開設の勅諭・大日本帝国憲法・帝国議会)' },
  { era:'近代', topic:'条約改正と日清・日露戦争(不平等条約の改正・下関条約・三国干渉・ポーツマス条約)' },
  { era:'近代', topic:'近代産業の発展(松方財政・産業革命・財閥の形成・労働運動と社会問題)' },
  // 現代
  { era:'現代', topic:'第一次世界大戦と日本(対華二十一カ条の要求・大戦景気・ワシントン体制)' },
  { era:'現代', topic:'大正デモクラシーと政党内閣(護憲運動・原敬内閣・普通選挙法・治安維持法)' },
  { era:'現代', topic:'満州事変から日中戦争へ(柳条湖事件・国際連盟脱退・二・二六事件・国家総動員法)' },
  { era:'現代', topic:'戦後改革と独立(GHQの占領政策・日本国憲法・農地改革・サンフランシスコ平和条約)' },
]

const COMMON = `# 厳守ルール（共通テスト 歴史総合・日本史探究）
- 2026 共通テスト 日本史探究と同一形式・同一難易度・同一語彙レベル(高校日本史)。
- ★★史実は教科書レベルで確実・正確に。年代・人物・事件・制度・因果関係を正しく。曖昧/マニアック/諸説ある事項は使わず、通説の確実な事実だけを用いる。時代錯誤(アナクロニズム)厳禁。少しでも不確かな事実は出さない。
- 出力は passage(導入文＋必要なら短い資料) と questions(設問配列) のみ。
- ★図・絵画・屏風絵・地図・写真・グラフ・パネル図に依存しない。資料を使う場合は「現代語訳された短い文書」か「数値の箇条書き/表」など文字情報のみ(本文テキストだけで解けること)。
- すべて単一正答の四択。組合せ問題は選択肢に全組合せを列挙する:
  ・下線部正誤組合せ → 選択肢「あ-X / あ-Y / い-X / い-Y」
  ・二文の正誤判定 → 選択肢「あ-正 い-正 / あ-正 い-誤 / あ-誤 い-正 / あ-誤 い-誤」
  ・疑問×考察 → 「あ-W / あ-Z / い-W / い-Z」等の組合せ
  ・年代整序 → 「ア→イ→ウ」等の完全な並びを4つ提示し正しい並びは1つ
  ・空欄補充組合せ → 「ア=○ イ=△」式
- 正答は唯一最良・他は明確に誤り。複数正答/正答なし/本文との矛盾は厳禁。
- explanation は「【単元】<時代>。正解は「<正答の選択肢テキストそのまま>」。」で始め、続けて日本史の事実で根拠を説明(なぜ正答か＋各誤答がなぜ誤りか=人物違い/年代違い/制度の誤り/時代錯誤 等を具体的に)。
- unit は時代(古代/中世/近世/近代/現代)。answer は choices の0始index(整数)。
- ★★正答位置を分散させる: 正誤組合せ・正誤判定では、文あ・い(X・Y)の正誤を意図的に変え(両方正/一方のみ誤/両方誤 をバランスよく作り)、正答が①(両方正)に偏らないようにする。1つの大問の中で、4問の正答が同じ番号に集中しないこと(①〜④に散らす)。年代整序・知識四択でも正答の位置を散らす。
- ★解説では『1つ目』『2つ目』『最後の選択肢』『選択肢1』『①』のような"位置"を指す表現を使わず、選択肢の内容(語句・記号あ/い/X/Y/W/Z)で説明する。`

const FORMAT_INSTR = `日本史探究の大問を1つ作る。指定テーマについて、導入文(会話文または説明・100〜220字)＋必要なら現代語訳資料(短文)を passage に置く。設問はちょうど4問・各単一正答の四択。次の型を必ず2型以上混ぜる: ①下線部あ・いとX・Yの正誤組合せ ②二文の正誤判定組合せ ③出来事の年代整序(3〜4件) ④疑問あ・い×考察W/X/Y/Z(または空欄補充の組合せ) ⑤文脈中の知識四択。教科書頻出の確実な事実のみを使い、各誤答も「ありがちな誤り(人物/年代/制度の取り違え)」にする。`

const AUTHOR_SCHEMA = {
  type:'object',
  properties:{
    passage:{type:'string'},
    questions:{type:'array', items:{
      type:'object',
      properties:{ stem:{type:'string'}, choices:{type:'array', items:{type:'string'}, minItems:4}, answer:{type:'integer'}, unit:{type:'string'}, explanation:{type:'string'} },
      required:['stem','choices','answer','unit','explanation']
    }}
  },
  required:['passage','questions']
}
const BLIND_SCHEMA = { type:'object', properties:{ answers:{type:'array', items:{type:'integer'}} }, required:['answers'] }
const REVIEW_SCHEMA = { type:'object', properties:{ daimon_blocker:{type:'boolean'}, reasons:{type:'array', items:{type:'string'}}, bad_questions:{type:'array', items:{type:'integer'}} }, required:['daimon_blocker','reasons','bad_questions'] }

function authorPrompt(item){
  return `${COMMON}\n\n# 形式\n${FORMAT_INSTR}\n\n# テーマ(時代=${item.era})\n${item.topic}\n\n上記を厳守し、本番同等の日本史探究の大問を1つ作成して passage と questions(4問・unit=${item.era}) を返してください。`
}
function buildView(d){
  let v = `【本文(導入・資料)】\n${d.passage}\n\n【設問】`
  d.questions.forEach((q,j)=>{ v += `\n\n問${j+1}: ${q.stem}`; q.choices.forEach((c,k)=> v += `\n  [${k}] ${c}`) })
  return v
}
function buildFull(d){
  let v = `【本文(導入・資料)】\n${d.passage}\n\n【設問・正答・解説】`
  d.questions.forEach((q,j)=>{ v += `\n\n問${j+1}(配列index ${j}): ${q.stem}`; q.choices.forEach((c,k)=> v += `\n  [${k}]${k===q.answer?' ★正答':''} ${c}`); v += `\n  解説: ${q.explanation}\n  unit: ${q.unit}` })
  return v
}
const STRATS = [
  'あなたは日本史が得意な受験生です。各設問を高校日本史の知識で丁寧に解いてください。',
  'まず明らかに史実に反する選択肢を消去し、残りを年代・人物・制度の知識で確定してください。',
  '各組合せ/各文について、それが史実として正しいか誤りかを一つずつ判定してから最終解答を選んでください。',
]
function solvePrompt(view, strat, n){
  return `${strat}\n\n${view}\n\n各問について選んだ選択肢の0始まりindex(整数)を、設問の順に answers 配列で返してください。設問数は ${n} 問です。`
}
const LENSES = [
  '【史実正確性レンズ】高校日本史の教科書・通説に照らし、各設問の★正答と各選択肢の主張(年代/人物/事件/制度/因果)が正しいかを一つずつ厳密に検証せよ。年代の前後関係の誤り、人物の取り違え、制度の説明の誤り、時代錯誤(アナクロニズム)、諸説あって断定できない事項を検出。少しでも事実が怪しい・通説と異なる・断定できない設問は bad_questions に入れる。',
  '【正答妥当性レンズ】各問の★正答が唯一最良で、他選択肢が明確に誤りか。組合せ/正誤判定/年代整序の選択肢が網羅的で、複数正答・正答なし・重複が無いか。explanation が正答選択肢テキストと一致し、根拠が妥当か。整序問題の並びが史実の年代順として正しいか。',
  '【自己完結・形式・難易度レンズ】図/絵画/屏風絵/地図/写真/グラフに依存せず、passage(導入・資料)と選択肢の文字情報＋高校日本史知識だけで全問解けるか。本番日本史探究の形式(組合せ/正誤/整序/疑問×考察)に忠実か。共通テスト本番相当の難易度か(易しすぎ/マニアックすぎない)。',
]
function reviewPrompt(lens, d){
  return `あなたは共通テスト日本史の作問校閲者です。次の自作大問(日本史探究の類似問題)を、特に次の観点で厳密に校閲してください。\n${lens}\n出力: daimon_blocker(大問ごと破棄すべき致命的問題があれば true)、reasons(具体的理由)、bad_questions(破棄すべき個別設問の0始まりindex配列・無ければ空配列)。史実が少しでも怪しい場合は迷わず bad_questions/daimon_blocker にすること。\n\n${buildFull(d)}`
}

const results = await pipeline(
  ITEMS,
  (item, _o, idx) => agent(authorPrompt(item), { label:`author:${item.era}#${idx}`, phase:'Author', schema:AUTHOR_SCHEMA, effort:'high' })
    .then(d => ({ item, idx, daimon:d })).catch(()=>null),
  async (prev) => {
    if(!prev || !prev.daimon || !Array.isArray(prev.daimon.questions) || !prev.daimon.questions.length) return null
    const { daimon, item, idx } = prev
    const view = buildView(daimon)
    const key = daimon.questions.map(q=>q.answer)
    const solves = await parallel(STRATS.map((s,k)=> ()=> agent(solvePrompt(view, s, daimon.questions.length), { label:`solve${k+1}:${item.era}#${idx}`, phase:'Solve', schema:BLIND_SCHEMA, effort:'high' })))
    const ok = solves.filter(Boolean)
    const keepFlags = key.map((kk,j)=> ok.length===3 && ok.every(s=> Array.isArray(s.answers) && s.answers[j]===kk))
    return { ...prev, keepFlags }
  },
  async (prev) => {
    if(!prev || !prev.daimon) return null
    const { daimon, keepFlags, item, idx } = prev
    const kept = daimon.questions.filter((_,j)=> keepFlags[j])
    if(kept.length < 3) return { dropped:true, reason:`blind-solve残り${kept.length}<3`, item, idx }
    const trimmed = { passage:daimon.passage, questions:kept }
    const revs = (await parallel(LENSES.map((lens,k)=> ()=> agent(reviewPrompt(lens, trimmed), { label:`review${k+1}:${item.era}#${idx}`, phase:'Review', schema:REVIEW_SCHEMA, effort:'high' })))).filter(Boolean)
    // 史実重視: blocker は1票でも大問破棄。bad_questions は1票でも該当小問破棄(高precision)。
    if(revs.some(r=>r.daimon_blocker)) return { dropped:true, reason:'review blocker', reasons:revs.flatMap(r=>r.reasons||[]).slice(0,8), item, idx }
    const bad = new Set(); revs.forEach(r=> (r.bad_questions||[]).forEach(bi=> bad.add(bi)))
    const finalQ = kept.filter((_,j)=> !bad.has(j))
    if(finalQ.length < 3) return { dropped:true, reason:`review残り${finalQ.length}<3`, item, idx }
    const qs = finalQ.map((q,j)=>({ id:`nh-tankyu-${idx}-${j}`, type:'multiple_choice', stem:q.stem, choices:q.choices, answer:q.answer, unit:q.unit||item.era, explanation:q.explanation }))
    return { dropped:false, era:item.era, row:{
      exam_id:'daigaku', part_key:'nihonshi', eiken_grade:'kyotsu', model:MODEL,
      question_data:{ passage:daimon.passage, subject:'社会', univ_simulated:'共通テスト', year_simulated:2026, source:SOURCE, format_type:'NIHONSHI_TANKYU', questions:qs }
    } }
  }
)

const ok = results.filter(Boolean)
const verified = ok.filter(r=>!r.dropped)
const dropped = ok.filter(r=>r.dropped).map(r=>({ era:r.item&&r.item.era, idx:r.idx, reason:r.reason, reasons:r.reasons }))
log(`authored=${ITEMS.length} verified=${verified.length} dropped=${dropped.length}`)
return JSON.stringify({ authored:ITEMS.length, verified:verified.length, dropped, rows:verified.map(v=>v.row) })
