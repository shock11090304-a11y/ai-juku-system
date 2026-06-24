export const meta = {
  name: 'eng-kyotsu2026-graph',
  description: '共テ英語 第8問(意見統合+Source A記事+Source Bグラフ)を本番難易度で作問→3盲ソルバー一致+3視点レビュー→検証済みrow(figure_svg込)をJSONで返す',
  phases: [
    { title: 'Author', detail: '長文(複数意見+記事)+グラフ+統合設問を作問' },
    { title: 'Solve', detail: '3名が本文+グラフ(数値テキスト)で盲解答しキー一致を検証' },
    { title: 'Review', detail: '3視点(自己完結/正答妥当/形式忠実/難易度)で校閲' },
  ],
}

const SOURCE = 'kyotsu-eng2026-graph2-20260624'
const MODEL = 'claude-eng2026-verified'

// 本番第8問のような賛否・観点が割れる議論テーマ
const ITEMS = [
  { topic: 'スマートフォンを学校に持ち込むことの是非(学習/連絡/集中/依存)' },
  { topic: '高校生が部活動と勉強を両立すべきか/部活の時間を減らすべきか' },
  { topic: '紙の本と電子書籍、学習にはどちらが良いか' },
  { topic: '学校の制服は必要か、私服を認めるべきか' },
  { topic: 'オンライン授業と対面授業、これからの学びにどちらを重視すべきか' },
  { topic: '地域の観光振興は住民にとって良いことか(経済 vs 混雑・環境)' },
]

const COMMON = `# 厳守ルール（共通テスト2026 第8問を本番そのままの構成・難易度で）
- 英語は高校卒業レベル(CEFR A2〜B1)・自然で文法的に正しいこと。ただし「本番の第8問」相当の長さ・読み応え・難易度にすること。
- passage は次の構成にする(全体で英語 480〜650語):
  1) 導入1〜2文: あるテーマについてエッセイ/レポートを書くプロジェクトで、級友の意見と2つの資料を集めた、という枠組み。
  2) 4〜5人の名前付き意見: 各 70〜100語の段落。立場・観点・理由が互いに異なり(賛成/反対/条件付き 等)、単なる事実でなく「意見」であること。
  3) **Source A**: 110〜150語の短い記事/専門家の説明(事実・研究・背景で論点を補強。意見ではなく情報)。
  4) **Source B**: 調査データ。本文では "Source B (the graph below)" 等で参照し、数値は本文に書かず「chart」に構造化する。
- chart は棒グラフ: title(英語), y_unit(例 "%"), categories(3〜6・短いラベル), series(1〜3・各 {name, values})。
- 設問はちょうど5問・各四択(単一正答)。**本番の難易度**を厳守:
  Q1: ある人物の意見の「趣旨」を最もよく表すもの(語句の表層一致でなく要旨理解)。
  Q2: 2人(以上)に共通する考え、または対立点。
  Q3: ある立場を最も強く支持する「2人の組合せ」を1択(「AとB」式)で、または誰の意見がSource Aと整合するか。
  Q4: Source A に基づく推論/要約(記事の主旨から導ける結論。記事の一文の言い換えだけにしない)。
  Q5: Source B(グラフ)に基づくが、**単なる最大/最小/差の読み取りは禁止**。データを本文の主張や人物の意見と結びつけ「最もよく支持される/示唆される記述」を選ばせる。誤答はもっともらしい誤読(因果の取り違え・一部だけ見る・過度の一般化)にする。
- 「小学生がグラフの数字だけで解ける」単純設問は禁止。各設問は本文/Source A/Source B の読解と統合を要すること。
- 正答は唯一最良・他は明確に誤り。複数正答/正答なし/本文やグラフとの矛盾は厳禁。
- explanation は「正解は「<正答の選択肢テキストそのまま>」。」で始め、日本語で根拠(誰の発言/記事のどこ/グラフのどの数値とどう結びつくか)を述べる。
- unit は技能ラベル(意見要旨/共通点把握/立場の統合/Source A推論/グラフと主張の統合 等)。answer は0始まりindex。正答位置は問ごとに変える。`

const AUTHOR_SCHEMA = {
  type:'object',
  properties:{
    passage:{type:'string'},
    chart:{ type:'object', properties:{
      title:{type:'string'}, y_unit:{type:'string'},
      categories:{type:'array', items:{type:'string'}, minItems:3},
      series:{type:'array', items:{ type:'object', properties:{ name:{type:'string'}, values:{type:'array', items:{type:'number'}} }, required:['name','values'] }, minItems:1}
    }, required:['title','y_unit','categories','series'] },
    questions:{type:'array', items:{
      type:'object',
      properties:{ stem:{type:'string'}, choices:{type:'array', items:{type:'string'}, minItems:4}, answer:{type:'integer'}, unit:{type:'string'}, explanation:{type:'string'} },
      required:['stem','choices','answer','unit','explanation']
    }}
  },
  required:['passage','chart','questions']
}
const BLIND_SCHEMA = { type:'object', properties:{ answers:{type:'array', items:{type:'integer'}} }, required:['answers'] }
const REVIEW_SCHEMA = { type:'object', properties:{ daimon_blocker:{type:'boolean'}, reasons:{type:'array', items:{type:'string'}}, bad_questions:{type:'array', items:{type:'integer'}} }, required:['daimon_blocker','reasons','bad_questions'] }

function chartToText(ch){
  if(!ch || !Array.isArray(ch.categories)) return ''
  const s = ch.series||[]
  let t = `【Source B グラフ】${ch.title||''}${ch.y_unit?` (単位: ${ch.y_unit})`:''}\n`
  if(s.length===1){ ch.categories.forEach((c,i)=>{ t += `  ${c}: ${s[0].values[i]}\n` }) }
  else { t += '  項目 | ' + s.map(x=>x.name).join(' | ') + '\n'; ch.categories.forEach((c,i)=>{ t += `  ${c} | ` + s.map(x=>x.values[i]).join(' | ') + '\n' }) }
  return t
}
function chartToSvg(ch){
  if(!ch || !Array.isArray(ch.categories) || !ch.categories.length || !Array.isArray(ch.series) || !ch.series.length) return ''
  const cats = ch.categories, series = ch.series
  const W=460, H=290, padL=48, padR=16, padT=38, padB=58
  const plotW = W-padL-padR, plotH = H-padT-padB
  const vals = series.flatMap(s=>(s.values||[]).map(Number)).filter(v=>!isNaN(v))
  const maxV = Math.max(1, ...vals)
  const pow = Math.pow(10, Math.floor(Math.log10(maxV)))
  let step = pow; if(maxV/pow <= 2) step = pow/5; else if(maxV/pow <= 5) step = pow/2
  let ymax = Math.ceil(maxV/step)*step
  if(ch.y_unit==='%' && maxV<=100) ymax = Math.min(100, Math.ceil(maxV/20)*20)
  if(ymax<=0) ymax = maxV
  const colors=['#60a5fa','#fbbf24','#34d399','#f0997b']
  const esc=s=>String(s==null?'':s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))
  let svg = `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" font-family="sans-serif">`
  const unitTag = ch.y_unit ? '(' + ch.y_unit + ')' : ''
  const _t = String(ch.title || '')
  const _appendUnit = unitTag && _t.indexOf('(') < 0 && _t.toLowerCase().indexOf(String(ch.y_unit).toLowerCase()) < 0
  const titleFull = _t + (_appendUnit ? ' ' + unitTag : '')
  if(titleFull) svg += `<text x="${W/2}" y="18" fill="#e5e7eb" font-size="13" text-anchor="middle">${esc(titleFull)}</text>`
  svg += `<line x1="${padL}" y1="${padT}" x2="${padL}" y2="${padT+plotH}" stroke="#9aa0a6" stroke-width="1"/>`
  svg += `<line x1="${padL}" y1="${padT+plotH}" x2="${padL+plotW}" y2="${padT+plotH}" stroke="#9aa0a6" stroke-width="1"/>`
  ;[0,0.5,1].forEach(f=>{ const y=padT+plotH-f*plotH; const val=Math.round(ymax*f*10)/10; svg += `<line x1="${padL}" y1="${y.toFixed(1)}" x2="${padL+plotW}" y2="${y.toFixed(1)}" stroke="#3a3a3a" stroke-width="0.5"/><text x="${padL-6}" y="${(y+3.5).toFixed(1)}" fill="#9aa0a6" font-size="10" text-anchor="end">${val}</text>` })
  const groupW = plotW/cats.length, ns = series.length
  const barW = Math.min(38, (groupW*0.72)/ns)
  cats.forEach((c,ci)=>{
    const gx = padL + ci*groupW + groupW/2
    series.forEach((s,si)=>{
      const v = Number(s.values[ci])||0
      const h = Math.max(0,(v/ymax)*plotH)
      const x = gx - (ns*barW)/2 + si*barW
      const y = padT+plotH-h
      svg += `<rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${barW.toFixed(1)}" height="${h.toFixed(1)}" fill="${colors[si%colors.length]}"/>`
      svg += `<text x="${(x+barW/2).toFixed(1)}" y="${(y-3).toFixed(1)}" fill="#e5e7eb" font-size="9.5" text-anchor="middle">${esc(v)}</text>`
    })
    svg += `<text x="${gx.toFixed(1)}" y="${(padT+plotH+16).toFixed(1)}" fill="#cbd5e1" font-size="10.5" text-anchor="middle">${esc(c)}</text>`
  })
  if(ns>1){ const ly=H-14; let lx=padL; series.forEach((s,si)=>{ svg += `<rect x="${lx}" y="${ly-9}" width="11" height="11" fill="${colors[si%colors.length]}"/><text x="${lx+15}" y="${ly}" fill="#cbd5e1" font-size="10.5">${esc(s.name)}</text>`; lx += 26 + String(s.name||'').length*6.6 }) }
  return svg + '</svg>'
}

function authorPrompt(item){
  return `${COMMON}\n\n# 議論テーマ\n${item.topic}\n\n上記ルールを厳守し、本番第8問と同等の長さ・難易度の大問を1つ作成して passage・chart・questions(5問)を返してください。`
}
function buildView(d){
  let v = `【本文】\n${d.passage}\n\n${chartToText(d.chart)}\n【設問】`
  d.questions.forEach((q,j)=>{ v += `\n\n問${j+1}: ${q.stem}`; q.choices.forEach((c,k)=> v += `\n  [${k}] ${c}`) })
  return v
}
function buildFull(d){
  let v = `【本文】\n${d.passage}\n\n${chartToText(d.chart)}\n【設問・正答・解説】`
  d.questions.forEach((q,j)=>{ v += `\n\n問${j+1}(index ${j}): ${q.stem}`; q.choices.forEach((c,k)=> v += `\n  [${k}]${k===q.answer?' ★正答':''} ${c}`); v += `\n  解説: ${q.explanation}\n  unit: ${q.unit}` })
  return v
}
const STRATS = [
  '丁寧に各人の意見・Source A・Source Bを読み、本文に明確な根拠があるものを選ぶこと。',
  'まず明らかに誤りの選択肢を消去法で除外し、残りを本文・記事・グラフと照合すること。',
  '各選択肢について誰の発言/記事のどこ/グラフのどの数値が根拠かを特定し、最も強いものを選ぶこと。',
]
function solvePrompt(view, strat, n){
  return `あなたは共通テスト英語(第8問)を解く受験者です。本文(複数の意見+Source A記事)とSource Bグラフ(数値はテキストで提示)と設問を読み、各設問について与えられた情報だけを根拠に最も適切な選択肢を1つ選んでください。${strat}\n\n${view}\n\n各問の選んだ選択肢の0始まりindexを設問順に answers 配列(整数)で返してください。設問数は ${n} 問です。`
}
function reviewPrompt(d){
  return `あなたは共通テスト英語の作問校閲者です。次の自作大問(第8問・意見統合+Source A記事+Source Bグラフ)を厳密に校閲してください。グラフはここで提示する数値から決定的に描画され生徒に表示されます。判定観点:\n1) 自己完結性: 本文+Source A+グラフ(数値)+選択肢だけで全問解けるか。\n2) 正答妥当性: 各問の★正答が唯一最良で他は明確に誤りか。複数正答/正答なし/矛盾が無いか。explanationが正答テキストと一致するか。\n3) 形式忠実性: 本番第8問の構成(複数意見+記事+グラフ+統合設問)に沿うか。\n4) **難易度**: 共通テスト本番相当か。特にグラフ設問が「最大/最小/差を読むだけ」の小学生レベルになっていないか(なっていれば bad_questions に入れる)。各設問が読解・統合を要するか。\n5) 英語の自然さ・文法・数値整合。\n出力: daimon_blocker(致命的なら true)、reasons、bad_questions(破棄すべき設問の0始まりindex・無ければ空)。\n\n${buildFull(d)}`
}

const results = await pipeline(
  ITEMS,
  (item, _o, idx) => agent(authorPrompt(item), { label:`author#${idx}`, phase:'Author', schema:AUTHOR_SCHEMA, effort:'high' })
    .then(d => ({ item, idx, daimon:d })).catch(()=>null),
  async (prev) => {
    if(!prev || !prev.daimon || !Array.isArray(prev.daimon.questions) || !prev.daimon.questions.length) return null
    const { daimon, idx } = prev
    const view = buildView(daimon)
    const key = daimon.questions.map(q=>q.answer)
    const solves = await parallel(STRATS.map((s,k)=> ()=> agent(solvePrompt(view, s, daimon.questions.length), { label:`solve${k+1}#${idx}`, phase:'Solve', schema:BLIND_SCHEMA, effort:'medium' })))
    const ok = solves.filter(Boolean)
    const keepFlags = key.map((kk,j)=> ok.length===3 && ok.every(s=> Array.isArray(s.answers) && s.answers[j]===kk))
    return { ...prev, keepFlags }
  },
  async (prev) => {
    if(!prev || !prev.daimon) return null
    const { daimon, keepFlags, idx } = prev
    const kept = daimon.questions.filter((_,j)=> keepFlags[j])
    if(kept.length < 4) return { dropped:true, reason:`blind-solve残り${kept.length}<4`, idx }
    const trimmed = { passage:daimon.passage, chart:daimon.chart, questions:kept }
    const revs = (await parallel([0,1,2].map(k=> ()=> agent(reviewPrompt(trimmed), { label:`review${k+1}#${idx}`, phase:'Review', schema:REVIEW_SCHEMA, effort:'high' })))).filter(Boolean)
    if(revs.filter(r=>r.daimon_blocker).length>=2) return { dropped:true, reason:'review blocker', reasons:revs.flatMap(r=>r.reasons||[]).slice(0,6), idx }
    const badCount={}; revs.forEach(r=> (r.bad_questions||[]).forEach(bi=>{ badCount[bi]=(badCount[bi]||0)+1 }))
    const finalQ = kept.filter((_,j)=> (badCount[j]||0) < 2)
    if(finalQ.length < 4) return { dropped:true, reason:`review残り${finalQ.length}<4`, idx }
    const svg = chartToSvg(daimon.chart)
    if(!svg) return { dropped:true, reason:'chart svg生成失敗', idx }
    const qs = finalQ.map((q,j)=>({ id:`e26-graph2-${idx}-${j}`, type:'multiple_choice', stem:q.stem, choices:q.choices, answer:q.answer, unit:q.unit, explanation:q.explanation }))
    return { dropped:false, row:{
      exam_id:'daigaku', part_key:'r_long', eiken_grade:'kyotsu', model:MODEL,
      question_data:{ passage:daimon.passage, subject:'英語', univ_simulated:'共通テスト', year_simulated:2026, source:SOURCE, format_type:'FMT_GRAPH8', figure_svg:svg, chart_data:daimon.chart, questions:qs }
    } }
  }
)

const ok = results.filter(Boolean)
const verified = ok.filter(r=>!r.dropped)
const dropped = ok.filter(r=>r.dropped).map(r=>({ idx:r.idx, reason:r.reason, reasons:r.reasons }))
log(`authored=${ITEMS.length} verified=${verified.length} dropped=${dropped.length}`)
return JSON.stringify({ authored:ITEMS.length, verified:verified.length, dropped, rows:verified.map(v=>v.row) })
