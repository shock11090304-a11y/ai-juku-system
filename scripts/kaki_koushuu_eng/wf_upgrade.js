export const meta = {
  name: 'kaki-eng-upgrade-difficulty',
  description: '文法の標準/入試ティアを高難度に作り替え（高校=MARCH/早慶旧帝, 中学=難関私国立高）',
  phases: [{ title: 'Upgrade', detail: '10文法セッションの標準(+高校は入試)ティアを再生成' }],
}

const ROOT = '/Users/adachishouhei/ai-juku-system/scripts/kaki_koushuu_eng'

const QTYPES = `
問題オブジェクトの型（"type" 必須・既存ファイルと同一スキーマ）:
- mc:      {"type":"mc","stem":"<英文。空所は ______>","note":"<和訳ヒント(任意)>","choices":["..","..","..",".."],"ans":<0起点idx>,"point":"<論点タグ>","exp":"<和訳解説>"}
- fill:    {"type":"fill","stem":"<英文 ______ 含む。( hint )可>","ans":"<入る語句>","point":"..","exp":".."}
- order:   {"type":"order","ja":"<和文>","tokens":["<チップ>",...],"ans":"<完成文・末尾ピリオド無し>","point":"..","exp":".."}
- error:   {"type":"error","html":"[a|..] .. [b|..] .. [c|..] .. [d|..]","ans":"c","correct":"x → y","point":"..","exp":".."}
- rewrite: {"type":"rewrite","given":"<英文>","target":"<英文 ______ 含む>","blanks":["..",".."],"point":"..","exp":".."}
- ja2en:   {"type":"ja2en","ja":"<和文>","models":["<模範解答1>","<模範解答2(任意)>"],"point":"<採点ポイント>","mistakes":"<よくあるミス>","lines":2}
【厳守】英文はネイティブ品質・正解は一義的に正しく誤答は明確に誤り／mcの ans は同一配列内で①②③④に散らす／order は tokens を並べ替えて ans に一致（空白連結の語集合が句読点除いて一致）／rewrite は target の ______ 数と blanks 数一致／error は下線3〜4か所／絵文字禁止／解説は「なぜそうなるか」を必ず。`

// 各セッション: key, level, regen（再生成するティア）, topic
const SESS = [
  // 高校: 標準=MARCH, 入試=早慶・旧帝
  { key:'kou_g1', level:'kou', topic:'文型と動詞（5文型・自動詞/他動詞・SVOC・使役/知覚・群動詞）' },
  { key:'kou_g2', level:'kou', topic:'時制・態・助動詞（各種完了・時/条件の副詞節・群動詞の受動態・助動詞+have p.p.・助動詞の語法）' },
  { key:'kou_g3', level:'kou', topic:'準動詞（不定詞・動名詞・分詞・分詞構文／完了形・意味上の主語・慣用表現）' },
  { key:'kou_g4', level:'kou', topic:'関係詞・接続詞・比較（前置詞+関係代名詞・関係副詞・複合関係詞・名詞節・比較の重要構文）' },
  { key:'kou_g5', level:'kou', topic:'仮定法・倒置・省略・強調・否定（if省略倒置・wish/as if・but for・否定語頭倒置・強調構文・部分否定）' },
  // 中学: 標準のみ=難関私国立高
  { key:'chu_g1', level:'chu', topic:'be動詞・一般動詞・時制（現在/過去/未来/進行形・否定疑問・3単現・不規則過去）' },
  { key:'chu_g2', level:'chu', topic:'助動詞・不定詞・動名詞（各種助動詞・不定詞3用法・動名詞・疑問詞+to・It is...to）' },
  { key:'chu_g3', level:'chu', topic:'比較・受け身（比較級/最上級/原級・受動態・by以外の前置詞・書き換え）' },
  { key:'chu_g4', level:'chu', topic:'現在完了・関係代名詞（完了3用法・since/for・関係代名詞主格/目的格・接触節）' },
  { key:'chu_g5', level:'chu', topic:'間接疑問文・分詞（間接疑問の語順・分詞の後置修飾・分詞構文の入口）' },
]

const SPEC = {
  kou: {
    regen: 'hyojun,nyushi',
    hyojun: 'GMARCH・関関同立レベルの標準〜頻出問題。語法・熟語・構文の識別で差がつく良問。mc/order/rewrite を混ぜて6〜8問。',
    nyushi: '早稲田・慶應・東大・京大・一橋レベルの難問。微妙な語法差、高度な構文（倒置/省略/複雑な関係詞/仮定法の応用/強調・否定）、骨のある誤り指摘、歯ごたえのある和文英訳を含める。4〜5問。「受験生がうなる」難度に。',
    keep: 'no, date, title, goal, points, kiso をそのまま保持し、hyojun と nyushi を新しく作り替える。',
  },
  chu: {
    regen: 'hyojun',
    hyojun: '難関私国立高校（開成・筑駒・慶應女子・早大学院・灘・渋幕など）の標準〜応用レベル。中学文法の範囲内だが、ひねった適用・紛らわしい識別・語順の難所で差がつく良問。mc/order/rewrite を混ぜて6〜8問。従来の基礎問より明確に一段上。',
    keep: 'no, date, title, goal, points, kiso, nyushi をそのまま保持し、hyojun だけを新しく作り替える。',
  },
}

phase('Upgrade')
log(`文法${SESS.length}セッションの難度を引き上げ（高校=MARCH/早慶旧帝, 中学=難関私国立高）`)

const results = await parallel(SESS.map(s => async () => {
  const sp = SPEC[s.level]
  const path = `${ROOT}/data/${s.key}.json`
  const nyushiBlock = s.level === 'kou'
    ? `\n■ 入試チャレンジ(nyushi) を作り替える難度: ${sp.nyushi}` : ''
  const prompt =
`あなたは大手予備校の英語科・作問責任者。既存教材の演習ティアを「もっと歯ごたえのある難度」に作り替える。

対象ファイル（必ず最初にReadする）: ${path}
【レベル/範囲】${s.level === 'kou' ? '高校（大学受験）' : '中学（中3・高校受験）'}／${s.topic}

【この作業で作り替えるもの】${sp.regen}
${sp.keep}

■ 標準問題(hyojun) を作り替える難度: ${sp.hyojun}${nyushiBlock}

${QTYPES}

【重要な指針】
- 既存の points（ポイント整理）の範囲・テーマに沿いつつ、既存の kiso（基礎問）とは重複しない、より高度な問題にする。
- 難度は上げるが「悪問（重箱の隅・複数正解・曖昧）」にしない。正解は必ず一義に定まること。
- ${s.level === 'kou' ? '解説(exp)は関正生スタイル（核心の一言→なぜ→原則化・コアイメージ）。' : '解説(exp)は中学生が読んで分かるやさしい言葉で（ただし内容は難関校レベル）。'}
- mc の正解位置は①②③④に散らす。

【作業】
1) 既存ファイルをReadし、指定ティアだけを高難度に作り替える（保持指定のフィールドは1文字も変えない）。
2) Writeで ${path} に「更新後の完全なJSON」を保存（前後に説明文を書かない・既存を上書き）。
3) Bashで自己検証し、失敗したら直して再保存:
   cd ${ROOT} && python3 -c "import json;d=json.load(open('data/${s.key}.json'));print('OK ${s.key}',{k:len(d.get(k,[])) for k in ('kiso','hyojun','nyushi')})"
4) 返答は1行のみ: 「${s.key} DONE <print結果>」`
  const out = await agent(prompt, { label: `up:${s.key}`, phase: 'Upgrade' })
  return { key: s.key, out: (out || '').slice(-120) }
}))

return { total: SESS.length, results: results.filter(Boolean) }
