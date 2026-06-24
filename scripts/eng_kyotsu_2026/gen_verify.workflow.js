export const meta = {
  name: 'eng-kyotsu2026-generate-verify',
  description: '共通テスト2026英語に類似した大問を作問→3名独立盲ソルバー一致+3視点レビューで検証→検証済みrowをJSONで返す',
  phases: [
    { title: 'Author', detail: '各大問を本番形式で作問' },
    { title: 'Solve', detail: '3名の独立盲ソルバーがキー一致を検証' },
    { title: 'Review', detail: '3視点(自己完結/正答妥当/形式忠実)で校閲' },
  ],
}

// ★実行するバッチをここで選ぶ（編集して再invoke）
const RUN = 'all'

const SOURCE = 'kyotsu-eng2026-similar2-20260624'
const MODEL = 'claude-eng2026-verified'

const COMMON = `# 厳守ルール（全形式共通）
- 2026年 大学入学共通テスト 英語リーディングと「同一形式・同一難易度」。語彙/文構造は高校卒業レベル(CEFR A2〜B1)。英語はネイティブとして自然・文法的に正しいこと。
- 出力は passage(本文) と questions(設問配列) のみ。
- すべての設問は「単一正答の多肢選択(四択。組合せ問題は六択でも可)」。正答は明確に唯一最良で、他の選択肢は本文から明確に誤りと判断できること。複数正答・正答なし・本文との矛盾は厳禁。
- 図・写真・グラフ・音声に依存しない。本文テキストだけで全問解けること。必要な数値/データは本文に文章または箇条書きで inline する。
- explanation は必ず「正解は「<正答の選択肢テキストをそのまま>」。」で始め、続けて本文の該当箇所を引用/要約して日本語で根拠を述べる。
- unit は設問が測る技能の日本語ラベル(事実把握/詳細理解/推論/意図把握/要点把握/事実と意見の区別/時系列把握/情報統合/内容一致/語句の意味 など)。
- answer は choices の0始まりindex(整数)。正答位置は設問ごとに変える(全部を同じ位置にしない)。
- 本文内の固有名詞・数値・日付・人物設定は一貫させる(矛盾禁止)。
- ★本番の難易度を厳守: 表層の語句一致で解ける単純設問にしない。各設問は読解・推論・複数情報の統合を要し、誤答は「もっともらしい誤読」(本文の一部だけ見る/因果の取り違え/別人物の発言と混同/過度の一般化/言い過ぎ)にする。1〜2語の置換で答えが分かる設問や「どれが一番〜?」式の単純設問は禁止。
- ★本番の語数を満たす: 各形式の指示語数の下限を必ず満たし、短くしない(第1問の短文だけは指示通り短く)。意見・コメント・説明は具体的な理由/経験/例を伴う充実した段落にする。`

const FORMAT_SPECS = {
  FMT1: { label:'第1問 短文・対話', part_key:'r_short', numQ:3, minKeep:2, instr:
`第1問型(短文・対話/掲示)。本文は次のいずれか1つ: ①4〜6人の友人/同級生によるテキストメッセージ(チャット)のやり取り、②学校・地域の掲示/お知らせ、③短いブログ/SNS投稿。150〜280語。設問は3問・各四択。技能例: 事実把握・詳細理解・推論(各人の立場/次にとる行動)。本番にある「画像を選ぶ」設問は作らない(全て文字情報だけで解く)。` },
  FMT2: { label:'第2問 調査・意見', part_key:'r_long', numQ:4, minKeep:3, instr:
`第2問型(調査・意見)。本文は「運営/学校/団体が投稿した告知または調査結果」＋「2名の利用者/学生の名前付きコメント(各70〜90語・理由や具体例を伴う)」。440〜530語。設問4問・各四択。必ず1問は「事実と意見の区別」(例: 〜の意見を最もよく表すのは/報告として事実なのは)。他は詳細理解・推論。コメント主の主張との一致/不一致を問う設問を含める。` },
  FMT3: { label:'第3問 物語＋順序', part_key:'r_long', numQ:3, minKeep:2, instr:
`第3問型(物語+順序)。一人称の体験談400〜480語(情景・心情・出来事を具体的に描写)。設問3問: (1)理由/きっかけを問う四択、(2)「出来事を起きた順に並べたものとして正しいのは」という"順序の組合せ"を1つ選ぶ設問(選択肢は「②→④→⑤→①」のような完全な並び順を4〜6個提示し、正しい並びは1つだけ・他は順序が崩れている)、(3)登場人物の心情/学び/形容詞を問う四択。物語内の出来事は明確な時系列を持たせる。` },
  FMT4: { label:'第4問 文章校正', part_key:'r_long', numQ:4, minKeep:3, instr:
`第4問型(文章校正)。本文は「生徒が書いた下書き(部誌/エッセイ/告知)」400〜480語。本文中の下線部を (1) (2) (3) (4) のように番号付きの語句で示し、文の挿入候補位置を <A> <B> <C> <D> として本文テキスト中に文字で埋め込む。本文の後に「Comments:」として指導者の指摘((1)〜(4)に対応)を載せる。設問4問・各四択: (1)下線部の後に続けるのに最適な語句、(2)与えられた1文を入れるのに最適な位置(選択肢は「<A>」「<B>」「<C>」「<D>」の4つ)、(3)下線部の文を置き換えるのに最適な文、(4)主旨をまとめる下線部を置き換えるのに最適な語句。挿入位置や下線は必ず本文中に文字として存在させ、図に頼らない。` },
  FMT5: { label:'第5問 複数資料統合', part_key:'r_long', numQ:5, minKeep:3, instr:
`第5問型(複数資料統合)。本文は3資料を連結: ①チラシ/リーフレット(イベント告知・条件付き箇条書き)、②記入済みのフォーム/申込み(複数エントリ。項目例: 名前/年/価格/作者/コメント)、③主催者からのメール。520〜620語。設問5問・各四択: 目的、内容真偽、複数エントリを横断する「組合せで正しい記述」(選択肢は「AとB」式の組合せを1択で選ぶ・六択可)、含まれない/該当しないもの、メールが依頼する事柄(「AとC」式の組合せ1択)。資料間の照合で解ける設計にする。` },
  FMT6: { label:'第6問 物語＋アウトライン', part_key:'r_long', numQ:4, minKeep:3, instr:
`第6問型(物語+アウトライン整理)。本文は物語520〜620語＋「Story Outline」(登場人物の特徴・重要な出来事・主題を整理する枠をテキストで提示)。設問4問・各四択または六択: (1)ある登場人物を最もよく表す「2つの組合せ」を1択で選ぶ(選択肢は「①と③」式・六択)、(2)出来事を起きた順に並べた"順序の組合せ"を1択(完全な並びを提示)、(3)ある人物について本文が伝えることを1択、(4)主人公について本文が伝える主題を1択。` },
  FMT7: { label:'第7問 論説＋スライド', part_key:'r_long', numQ:5, minKeep:3, instr:
`第7問型(学術論説+スライド/要点)。本文は一般向けの説明的論説(心理・脳科学・社会・健康・環境などの話題)520〜620語＋発表用スライドの下書き(見出しと空所のある箇条書きをテキストで提示)。設問5問・各四択または六択: (1)現象が起こる条件/時を1択、(2)効果/利点の「2つの組合せ」を1択(六択)、(3)ある段階で起きることを1択、(4)研究知見の要約を1択、(5)複数の人物プロフィール(生活習慣)を本文中に提示し、本文の助言に最も合致する「2人の組合せ」を1択(六択)。専門用語は本文で平易に説明する。` },
  FMT8: { label:'第8問 意見統合＋資料', part_key:'r_long', numQ:5, minKeep:3, instr:
`第8問型(意見統合+資料)。本文は「あるテーマ(スポーツと技術/SNSと社会/AIと教育/環境と消費 等)についての小論文プロジェクト」。複数の名前付き意見(4〜5名)＋ Source A(短い記事)＋ Source B(調査データ)。Source B のグラフは描かず、数値を本文に表または箇条書きで inline する(例:「靴の快適さ: 一般ランナー74%, 学生選手57%, プロ60%」)。540〜660語。設問5問・各四択: ある人物の意見の要約、2人に共通する意見、ある立場を最も支持する人物(「AとB」式の組合せ1択可)、Source A に基づく根拠、Source B(inlineデータ)に基づき結論を支持する記述。データ参照問題は本文の数値だけで判定できるようにする。` },
}

const BATCHES = {
  b1: [
    { format:'FMT1', topic:'学園祭の出し物を相談する4〜5人のチャット' },
    { format:'FMT1', topic:'部活の合宿の持ち物・集合を連絡するチャット' },
    { format:'FMT1', topic:'図書館の利用ルール変更を知らせる掲示' },
    { format:'FMT1', topic:'地域の清掃ボランティア募集のお知らせ' },
    { format:'FMT1', topic:'テスト前の勉強会の日程を決める友人のチャット' },
    { format:'FMT1', topic:'体育祭の係分担を相談するクラスのチャット' },
    { format:'FMT1', topic:'放課後の図書委員募集を知らせる学校の掲示' },
    { format:'FMT1', topic:'文化部の発表会への来場を呼びかける短いブログ投稿' },
  ],
  b2: [
    { format:'FMT2', topic:'学生寮の食堂満足度調査＋2名の学生コメント' },
    { format:'FMT2', topic:'図書館の開館時間変更の告知＋2名の利用者コメント' },
    { format:'FMT2', topic:'学校の制服方針見直しのアンケート結果＋2名の生徒コメント' },
    { format:'FMT2', topic:'オンライン授業の受講者フィードバック調査＋2名のコメント' },
    { format:'FMT2', topic:'市民ジムの会員満足度調査＋2名の会員コメント' },
    { format:'FMT3', topic:'初めての料理教室での失敗と学び' },
    { format:'FMT3', topic:'落とし物を届けて感謝された親切の話' },
    { format:'FMT3', topic:'泳げるようになるまでの練習の話' },
    { format:'FMT3', topic:'飼っていた小動物から学んだことの話' },
    { format:'FMT3', topic:'部活の大会で緊張を乗り越えた話' },
  ],
  b3: [
    { format:'FMT4', topic:'エコ週間の活動を紹介する部誌の下書き' },
    { format:'FMT4', topic:'体育祭を盛り上げる告知の下書き' },
    { format:'FMT4', topic:'読書週間を紹介する図書委員の下書き' },
    { format:'FMT4', topic:'地域清掃の募金活動を呼びかけるエッセイの下書き' },
    { format:'FMT4', topic:'科学フェアの来場案内文の下書き' },
    { format:'FMT5', topic:'図書ブックフェア(チラシ＋推薦フォーム＋主催メール)' },
    { format:'FMT5', topic:'地域コミュニティガーデン(チラシ＋申込フォーム＋運営メール)' },
    { format:'FMT5', topic:'修学旅行のコース選択(案内＋希望フォーム＋担当メール)' },
    { format:'FMT5', topic:'科学クラブの発表会(募集チラシ＋応募フォーム＋顧問メール)' },
    { format:'FMT5', topic:'美術展のボランティア(募集チラシ＋登録フォーム＋主催メール)' },
  ],
  b4: [
    { format:'FMT6', topic:'商店街のパン屋の店主の無言の親切の物語' },
    { format:'FMT6', topic:'部活のコーチの厳しくも温かい教えの物語' },
    { format:'FMT6', topic:'祖母のレシピと家族のつながりの物語' },
    { format:'FMT6', topic:'職場の先輩(メンター)との関わりの物語' },
    { format:'FMT6', topic:'幼なじみとの思い出と再会の物語' },
    { format:'FMT7', topic:'睡眠の科学(なぜ眠りが学習に重要か)' },
    { format:'FMT7', topic:'音楽が脳と気分に与える効果' },
    { format:'FMT7', topic:'習慣はどのように形成されるか' },
    { format:'FMT7', topic:'好奇心が学びを促す力' },
    { format:'FMT7', topic:'なぜ人は忘れるのか(忘却の働き)' },
  ],
  b5: [
    { format:'FMT8', topic:'SNSと社会(つながりと注意散漫)' },
    { format:'FMT8', topic:'AIと教育(学習支援の利点と課題)' },
    { format:'FMT8', topic:'プラスチックと環境(使い捨ての是非)' },
    { format:'FMT8', topic:'リモートワークの是非' },
    { format:'FMT8', topic:'観光と地域文化(観光の功罪)' },
  ],
}

const AUTHOR_SCHEMA = {
  type:'object',
  properties:{
    passage:{type:'string'},
    questions:{type:'array', items:{
      type:'object',
      properties:{
        stem:{type:'string'},
        choices:{type:'array', items:{type:'string'}, minItems:4},
        answer:{type:'integer'},
        unit:{type:'string'},
        explanation:{type:'string'}
      },
      required:['stem','choices','answer','unit','explanation']
    }}
  },
  required:['passage','questions']
}
const BLIND_SCHEMA = { type:'object', properties:{ answers:{type:'array', items:{type:'integer'}} }, required:['answers'] }
const REVIEW_SCHEMA = { type:'object', properties:{
  daimon_blocker:{type:'boolean'},
  reasons:{type:'array', items:{type:'string'}},
  bad_questions:{type:'array', items:{type:'integer'}}
}, required:['daimon_blocker','reasons','bad_questions'] }

function authorPrompt(spec, item){
  return `${COMMON}\n\n# 今回の作問形式\n${spec.instr}\n\n# 題材ヒント\n${item.topic}\n\n設問数はちょうど ${spec.numQ} 問。上記ルールを厳守し、本番と同等品質の大問を1つ作成して passage と questions を返してください。`
}
function buildView(d){
  let v = `【本文】\n${d.passage}\n\n【設問】`
  d.questions.forEach((q,j)=>{ v += `\n\n問${j+1}: ${q.stem}`; q.choices.forEach((c,k)=> v += `\n  [${k}] ${c}`) })
  return v
}
function buildFull(d){
  let v = `【本文】\n${d.passage}\n\n【設問・正答・解説】`
  d.questions.forEach((q,j)=>{ v += `\n\n問${j+1}(配列index ${j}): ${q.stem}`; q.choices.forEach((c,k)=> v += `\n  [${k}]${k===q.answer?' ★正答':''} ${c}`); v += `\n  解説: ${q.explanation}\n  unit: ${q.unit}` })
  return v
}
const STRATS = [
  '丁寧に全選択肢を吟味し、本文に明確な根拠があるものを選ぶこと。',
  'まず明らかに誤りの選択肢を消去法で除外し、残りを本文と照合すること。',
  '各選択肢について本文中の該当文を特定できるか確認し、根拠が最も強いものを選ぶこと。',
]
function solvePrompt(view, strat, n){
  return `あなたは共通テスト英語を解く受験者です。本文と設問を読み、各設問について本文の情報だけを根拠に最も適切な選択肢を1つ選んでください。${strat}\n\n${view}\n\n各問について選んだ選択肢の0始まりindex(整数)を、設問の順に answers 配列で返してください。設問数は ${n} 問です。`
}
function reviewPrompt(spec, d){
  return `あなたは共通テスト英語の作問校閲者です。次の自作大問(本番2026 ${spec.label} 形式の類似問題)を厳密に校閲してください。判定観点:\n1) 自己完結性: 本文・設問・選択肢の文字情報だけで全問解けるか(図/写真/グラフ/音声に依存していないか)。\n2) 正答の妥当性: 各問の★正答が本当に唯一最良で、他選択肢は本文から明確に誤りか。複数正答・正答なし・本文との矛盾が無いか。explanation が正答選択肢テキストと一致しているか。\n3) 形式忠実性: ${spec.label} の本番形式に沿っているか。\n4) ★難易度: 共通テスト本番相当か。表層の語句一致や1〜2語置換で解ける単純設問、「どれが一番〜?」式の小学生レベルの設問になっていないか(なっていれば bad_questions に入れる)。各設問が読解・推論・統合を要し、誤答がもっともらしい誤読になっているか。${spec.part_key==='r_long'?'本文が第1問の短文でなく長文形式として十分な語数・読み応えがあるか。':'第1問の短文として適切か。'}\n5) 英語の自然さ・文法・固有名詞/数値/日付の整合。\n出力: daimon_blocker(大問ごと破棄すべき致命的問題があれば true)、reasons(理由)、bad_questions(破棄すべき個別設問の0始まりindex配列・無ければ空配列)。\n\n${buildFull(d)}`
}

BATCHES.rest = [].concat(BATCHES.b2, BATCHES.b3, BATCHES.b4, BATCHES.b5)
BATCHES.all = [].concat(BATCHES.b1, BATCHES.b2, BATCHES.b3, BATCHES.b4, BATCHES.b5)

const items = BATCHES[RUN] || []
const batch = RUN

const results = await pipeline(
  items,
  (item, _o, idx) => {
    const spec = FORMAT_SPECS[item.format]
    return agent(authorPrompt(spec, item), { label:`author:${item.format}#${idx}`, phase:'Author', schema:AUTHOR_SCHEMA, effort:'high' })
      .then(d => ({ item, spec, idx, daimon:d }))
      .catch(()=>null)
  },
  async (prev) => {
    if (!prev || !prev.daimon || !Array.isArray(prev.daimon.questions) || !prev.daimon.questions.length) return null
    const { daimon, item, idx } = prev
    const view = buildView(daimon)
    const key = daimon.questions.map(q=>q.answer)
    const solves = await parallel(STRATS.map((s,k)=> ()=>
      agent(solvePrompt(view, s, daimon.questions.length), { label:`solve${k+1}:${item.format}#${idx}`, phase:'Solve', schema:BLIND_SCHEMA, effort:'medium' })))
    const ok = solves.filter(Boolean)
    const keepFlags = key.map((kk,j) => ok.length===3 && ok.every(s=> Array.isArray(s.answers) && s.answers[j]===kk))
    return { ...prev, keepFlags }
  },
  async (prev) => {
    if (!prev || !prev.daimon) return null
    const { daimon, keepFlags, spec, item, idx } = prev
    const kept = daimon.questions.filter((_,j)=> keepFlags[j])
    if (kept.length < spec.minKeep) return { dropped:true, reason:`blind-solve残り${kept.length}<min${spec.minKeep}`, item, idx }
    const trimmed = { passage:daimon.passage, questions:kept }
    const revs = (await parallel([0,1,2].map(k=> ()=>
      agent(reviewPrompt(spec, trimmed), { label:`review${k+1}:${item.format}#${idx}`, phase:'Review', schema:REVIEW_SCHEMA, effort:'high' })))).filter(Boolean)
    const blockerVotes = revs.filter(r=>r.daimon_blocker).length
    if (blockerVotes>=2) return { dropped:true, reason:'review blocker', reasons:revs.flatMap(r=>r.reasons||[]).slice(0,6), item, idx }
    const badCount = {}
    revs.forEach(r=> (r.bad_questions||[]).forEach(bi=>{ badCount[bi]=(badCount[bi]||0)+1 }))
    const finalQ = kept.filter((_,j)=> (badCount[j]||0) < 2)
    if (finalQ.length < spec.minKeep) return { dropped:true, reason:`review残り${finalQ.length}<min${spec.minKeep}`, item, idx }
    const qs = finalQ.map((q,j)=>({ id:`e26-${batch}-${item.format}-${idx}-${j}`, type:'multiple_choice', stem:q.stem, choices:q.choices, answer:q.answer, unit:q.unit, explanation:q.explanation }))
    return { dropped:false, format:item.format, row:{
      exam_id:'daigaku', part_key:spec.part_key, eiken_grade:'kyotsu', model:MODEL,
      question_data:{ passage:daimon.passage, subject:'英語', univ_simulated:'共通テスト', year_simulated:2026, source:SOURCE, format_type:item.format, questions:qs }
    } }
  }
)

const ok = results.filter(Boolean)
const verified = ok.filter(r=>!r.dropped)
const dropped = ok.filter(r=>r.dropped).map(r=>({ format:r.item&&r.item.format, idx:r.idx, reason:r.reason, reasons:r.reasons }))
log(`batch=${batch} authored=${items.length} verified=${verified.length} dropped=${dropped.length}`)
return JSON.stringify({ batch, authored:items.length, verified:verified.length, dropped, rows:verified.map(v=>v.row) })
