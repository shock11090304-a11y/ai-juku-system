export const meta = {
  name: 'kaki-eng-generate',
  description: '夏期講習 英語テキスト 全20セッションの内容を生成しJSONで書き出す',
  phases: [{ title: 'Generate', detail: '20セッション(中学/高校 × 文法5/長文5)を並列生成' }],
}

const DATA = '/Users/adachishouhei/ai-juku-system/scripts/kaki_koushuu_eng/data'

const COMMON_RULES = `
【厳守ルール】
- 出力は必ず「有効なJSON」1個。日本語はそのままUTF-8で。絵文字は禁止（記号は ▲ ★ ● → のみ可）。
- 英文はすべて自然で文法的に正しいネイティブ英語。正解は一義的に正しく、誤答（distractor）は明確に誤りであること。
- mc の "ans" は 0 起点の正解インデックス。★同一セッション内で正解位置を①②③④に散らす（同じ位置に偏らせない）。
- order は tokens（語群チップ）を並べ替えると "ans"（完成文・末尾ピリオド無し）に一致すること。tokens を空白連結して語を分解した集合が ans の語集合と完全一致すること（句読点は無視）。
- error は英文中の下線を [a|語句] [b|語句] [c|語句] [d|語句] の形で3〜4か所付け、"ans" は誤りの記号、"correct" は "誤→正" の形。
- rewrite は target 中の ______（6アンダースコア）の数と "blanks" 配列の長さを一致させる。
- fill は stem 中に ______（6アンダースコア）を必ず入れ、"ans" に入る語句を書く。ヒント語は stem 内に ( play ) のように丸括弧で入れてよい。
- 解説（exp）は「なぜそうなるか」を必ず書く。`

const GRAMMAR_SCHEMA = `
【文法セッションJSONスキーマ】
{
  "no": <整数>, "date": "<M/D>", "title": "<講タイトル>",
  "goal": "<この講のねらい・日本語1文>",
  "points": [   // ポイント整理 3〜4個
    {"h":"<見出し>","body":"<説明・日本語>","ex":[["<English例文>","<和訳>"], ...1〜2], "rule":"<★一言ルール（任意）>"}
  ],
  "kiso":   [ <基礎問 6〜8題> ],   // ★必須。やさしく1論点ずつ。fill中心＋やさしいmc
  "hyojun": [ <標準問題 6〜8題> ], // mc / order / rewrite を混ぜる
  "nyushi": [ <入試チャレンジ 4〜5題> ] // error / 難しめmc・order / ja2en(和文英訳)
}
問題オブジェクトの型（"type" 必須）:
- {"type":"mc","stem":"<英文。空所は ______>","note":"<和訳ヒント(任意)>","choices":["..","..","..",".."],"ans":<0起点idx>,"point":"<短い論点タグ>","exp":"<和訳解説>"}
- {"type":"fill","stem":"<英文 ______ 含む。( hint ) 可>","ans":"<入る語句>","point":"..","exp":".."}
- {"type":"order","ja":"<和文>","tokens":["<チップ>",...],"ans":"<完成文・末尾ピリオド無し>","point":"..","exp":".."}
- {"type":"error","html":"[a|..] .. [b|..] .. [c|..] .. [d|..]","ans":"c","correct":"x → y","point":"..","exp":".."}
- {"type":"rewrite","given":"<英文>","target":"<英文 ______ 含む>","blanks":["..",".."],"point":"..","exp":".."}
- {"type":"ja2en","ja":"<和文>","models":["<模範解答1>","<模範解答2(任意)>"],"point":"<採点ポイント>","mistakes":"<よくあるミス>","lines":2}`

const READING_SCHEMA = `
【長文セッションJSONスキーマ】
{
  "no": <整数>, "date": "<M/D>", "title":"<講タイトル>",
  "goal":"<ねらい・日本語1文>",
  "points":[ {"h":"..","body":"..","ex":[["English","和訳"]],"rule":".."} ...2〜3 ],  // 読み方のコツ
  "passage":{
    "title":"<英語タイトル>","jtitle":"<和題>",
    "paras":[ ["<文1>","<文2>",...], ["<文>",...] ],  // 段落の配列。各段落は文（string）の配列。全文を通し番号で数える
    "trans":{ "1":"<文1の和訳>","2":"..", ... }  // ★全ての文番号(1..N)を必ず網羅
  },
  "vocab":[ ["<word>","<品詞: 名/動/形/副/熟>","<意味>"], ...6〜12 ],
  "q_instr":"<設問全体の指示(任意)>",
  "questions":[   // 5〜7問
    {"type":"rc_mc","q":"<設問・日本語。文(3)等で参照可>","choices":["..","..",".."],"ans":<0起点idx>,"exp":"<なぜ正解/他がなぜ誤り>"},
    {"type":"rc_desc","q":"<設問・日本語。例: 文(4)の主語Sと動詞Vを答えよ / 下線部を和訳せよ / itの指す内容を答えよ>","ans":"<模範解答・日本語>","exp":"..","lines":2}
  ]
}
- 英文パッセージは完全オリジナル・自然で正しい英語・指定語数・指定レベル。事実誤りを書かない。
- 各文は paras 内の出現順に (1)(2)... と数える。trans はその全番号を必ず埋める。
- 設問は本文だけで解答可能に。文番号で参照する。`

// key, kind, level(表示), minutes, brief
const SESSIONS = [
  // ---- 中学生版 文法 (中3 高校受験。基礎問を厚めに) ----
  { key:'chu_g1', kind:'grammar', level:'中学生（中3・高校受験）', brief:
    '第1講「be動詞・一般動詞・時制」7/27。範囲=現在/過去/未来(will・be going to)/現在進行形/過去進行形、be動詞と一般動詞の否定・疑問の区別、3単現のs、規則・不規則過去形。基礎問はbe/一般の区別と3単現・過去形の定着を最優先。標準で進行形と時制の使い分け、入試で難関私立レベルの時制判断＋和文英訳1題。解説は中学生が読んで分かるやさしい言葉で。' },
  { key:'chu_g2', kind:'grammar', level:'中学生（中3・高校受験）', brief:
    '第2講「助動詞・不定詞・動名詞」7/28。範囲=can/could/will/would/must/should/may/have to、不定詞の3用法(名詞/形容詞/副詞)、動名詞、want to do / enjoy doing、疑問詞+to do、It is ... to do。基礎問で助動詞と不定詞の形、標準で用法の識別、入試で動名詞/不定詞をとる動詞の区別＋和文英訳。やさしい解説。' },
  { key:'chu_g3', kind:'grammar', level:'中学生（中3・高校受験）', brief:
    '第3講「比較・受け身」7/29。範囲=比較級/最上級(-er/-est, more/most, better/best)、as ... as、not as ... as、比較の疑問文、受動態 be+過去分詞、by ...、受動態の否定・疑問、by以外の前置詞(be interested in等)。基礎問で比較変化と受け身の形、標準で書き換え、入試で難関私立レベル＋和文英訳。やさしい解説。' },
  { key:'chu_g4', kind:'grammar', level:'中学生（中3・高校受験）', brief:
    '第4講「現在完了・関係代名詞」7/30。範囲=現在完了(継続/経験/完了・結果 have+p.p.、since/for、ever/never/just/already/yet)、現在完了進行形の入口、関係代名詞(who/which/that 主格・目的格、接触節の入口)。基礎問で完了の3用法の形、標準で関係代名詞の選択、入試で難関私立＋和文英訳。やさしい解説。' },
  { key:'chu_g5', kind:'grammar', level:'中学生（中3・高校受験）', brief:
    '第5講「間接疑問文・分詞（後置修飾）／発展:分詞構文の入口」7/31。範囲=間接疑問文(I know what he wants / Do you know where she lives)、現在分詞・過去分詞の後置修飾(the boy running / a language spoken in ...)、発展として分詞構文の入口(難関私国立向け)。基礎問で間接疑問の語順と分詞の形、標準で後置修飾、入試で難関私立レベルの分詞構文＋和文英訳。やさしい解説だが発展は少し踏み込む。' },
  // ---- 中学生版 長文 (中3 高校受験レベル) ----
  { key:'chu_r1', kind:'reading', level:'中学生（中3・高校受験）', brief:
    '第1講「構造把握（英文解釈）」8/17。本文120〜160語・中3高校受験レベル(公立上位〜難関私立)・身近で読みやすい話題(習慣/学校/科学の入口など)。読み方ポイント=主語S・動詞Vの発見、修飾語を( )に入れる。設問5問=rc_descで特定文のS/Vを問う・短い和訳、rc_mcで大意。' },
  { key:'chu_r2', kind:'reading', level:'中学生（中3・高校受験）', brief:
    '第2講「論理展開・つなぎ言葉」8/18。本文130〜170語。読み方ポイント=but/so/because/however/for example などのつなぎ言葉を追う。設問5〜6問=空所に入るつなぎ語(rc_mc)、逆接/具体例/因果の把握(rc_mc)、指示語や大意。' },
  { key:'chu_r3', kind:'reading', level:'中学生（中3・高校受験）', brief:
    '第3講「設問処理」8/19。本文140〜180語。読み方ポイント=内容一致問題の解き方、指示語(it/they/this)の追い方、下線部の言い換え。設問6問=内容一致(rc_mc複数)、指示語の内容(rc_desc)、下線部和訳(rc_desc)。' },
  { key:'chu_r4', kind:'reading', level:'中学生（中3・高校受験）', brief:
    '第4講「速読トレーニング」8/20。本文130〜170語・やや易しめで一気に読める話題。読み方ポイント=スラッシュリーディング(意味のまとまりで区切る)、返り読みをしない。goalに目標時間の意識を入れる。設問5問=大意・段落の要点・順序(rc_mc中心)＋1問rc_desc。q_instrに「まず○分で通読」と入れる。' },
  { key:'chu_r5', kind:'reading', level:'中学生（中3・高校受験）', brief:
    '第5講「志望校別 実戦演習」8/21。本文160〜200語・難関公立/私立高校の入試レベル総合。読み方ポイント=これまでの総合(構造→論理→設問処理→速読)。設問6〜7問=内容一致・指示語・和訳・つなぎ語・大意をバランスよく(rc_mc/rc_desc混在)。' },
  // ---- 高校生版 文法 (大学受験。文型〜倒置・省略。基礎問入り) ----
  { key:'kou_g1', kind:'grammar', level:'高校生（大学受験）', brief:
    '第1講「文型と動詞（5文型・自動詞/他動詞・SVOC）」7/27。範囲=5文型(SV/SVC/SVO/SVOO/SVOC)、自動詞と他動詞の区別、第4文型→第3文型の書き換え、知覚動詞/使役動詞のSVOC、群動詞。基礎問で文型の判定と自他の区別、標準で書き換え・語法、入試でSVOC/使役・知覚＋和文英訳。解説は関正生スタイル(核心の一言→なぜ→原則化・コアイメージ)。' },
  { key:'kou_g2', kind:'grammar', level:'高校生（大学受験）', brief:
    '第2講「時制・態・助動詞」7/28。範囲=現在完了/過去完了/未来完了、進行形の可否、時・条件の副詞節中の現在形、受動態(群動詞の受動態/by以外)、助動詞+have p.p.(must/should/could/may have p.p.)、助動詞の語法。基礎問で完了と受動の形、標準で時制の一致・態、入試で助動詞+have p.p.＋和文英訳。関正生スタイル解説。' },
  { key:'kou_g3', kind:'grammar', level:'高校生（大学受験）', brief:
    '第3講「準動詞（不定詞・動名詞・分詞・分詞構文）」7/29。範囲=不定詞(名/形/副・完了不定詞・意味上の主語・too~to/enough to)、動名詞(動名詞のみ/不定詞のみをとる動詞・前置詞to)、分詞(限定/叙述・感情分詞)、分詞構文(付帯状況with・完了/否定/独立)。基礎問で形の識別、標準で動名詞/不定詞の選択、入試で分詞構文＋和文英訳。関正生スタイル解説。' },
  { key:'kou_g4', kind:'grammar', level:'高校生（大学受験）', brief:
    '第4講「関係詞・接続詞・比較」7/30。範囲=関係代名詞(格・所有格whose・前置詞+関係代名詞)、関係副詞(where/when/why/how)、非制限用法、複合関係詞(whatever等)、接続詞(等位/従位・名詞節that/if/whether)、比較(原級・比較級・最上級・比較を用いた重要表現 the 比較級/no more than 等)。基礎問で関係詞と接続詞の基本、標準で識別、入試で比較の重要構文＋和文英訳。関正生スタイル解説。' },
  { key:'kou_g5', kind:'grammar', level:'高校生（大学受験）', brief:
    '第5講「仮定法・倒置・省略・強調（否定含む）」7/31。範囲=仮定法過去/過去完了/未来、if省略の倒置、I wish/as if/without・but for、否定語頭の倒置(Hardly/Never/Not only)、強調構文It is ~ that、省略(as/though節)、部分否定/二重否定。基礎問で仮定法の基本形、標準で倒置・強調、入試で総合＋和文英訳。関正生スタイル解説。難度は高め(文型〜倒置・省略の総仕上げ)。' },
  // ---- 高校生版 長文 (大学受験 共通テスト〜MARCH/中堅国公立) ----
  { key:'kou_r1', kind:'reading', level:'高校生（大学受験）', brief:
    '第1講「構造把握（英文解釈）」8/17。本文200〜260語・評論調(教育/科学/社会など)・共通テスト〜MARCH下位レベル。読み方ポイント=SVOCの把握、名詞節/関係詞節/分詞のカタマリ処理、長い主語の見抜き。設問5〜6問=特定文のS/V/構造(rc_desc)、構造的に難しい文の和訳(rc_desc)、大意(rc_mc)。' },
  { key:'kou_r2', kind:'reading', level:'高校生（大学受験）', brief:
    '第2講「論理展開・つなぎ言葉」8/18。本文220〜280語・評論調。読み方ポイント=ディスコースマーカー(however/therefore/in contrast/for instance/moreover)、パラグラフの主題文と展開、抽象→具体。設問6問=空所に入るつなぎ語(rc_mc)、段落の論理関係、筆者の主張(rc_mc)、言い換え。' },
  { key:'kou_r3', kind:'reading', level:'高校生（大学受験）', brief:
    '第3講「設問処理」8/19。本文220〜280語。読み方ポイント=内容一致の選択肢処理(本文の言い換え・過度な一般化の罠)、空所補充、指示語、下線部言い換え。設問6〜7問=内容一致(rc_mc複数)、空所補充(rc_mc)、指示語の内容(rc_desc)、下線部の言い換え/和訳(rc_desc)。MARCHレベルの設問の作り。' },
  { key:'kou_r4', kind:'reading', level:'高校生（大学受験）', brief:
    '第4講「速読トレーニング」8/20。本文220〜280語・共通テスト型の読みやすい情報系/物語系。読み方ポイント=チャンク(意味のまとまり)読み、パラグラフリーディング(各段落1メッセージ)、設問先読み。goalとq_instrに目標時間(例:○分で通読)を入れる。設問6問=大意・要点・段落対応・事実照合(rc_mc中心)＋1問rc_desc。' },
  { key:'kou_r5', kind:'reading', level:'高校生（大学受験）', brief:
    '第5講「志望校別 実戦演習」8/21。本文260〜320語・MARCH〜中堅国公立レベルの評論。読み方ポイント=これまでの総合(構造→論理→設問処理→速読)。設問6〜7問=内容一致・空所補充・指示語・下線部和訳・主題をバランスよく(rc_mc/rc_desc混在)。歯ごたえのある実戦セット。' },
]

function schemaFor(kind) { return kind === 'grammar' ? GRAMMAR_SCHEMA : READING_SCHEMA }

phase('Generate')
log(`夏期講習 英語 全${SESSIONS.length}セッションを生成開始`)

const results = await parallel(SESSIONS.map(s => async () => {
  const path = `${DATA}/${s.key}.json`
  const prompt =
`あなたは大手予備校の英語科教材開発責任者。トリリオン夏期講習の英語テキスト1セッション分の中身を作る。

【レベル】${s.level}
【担当セッション】${s.brief}

${schemaFor(s.kind)}
${COMMON_RULES}

【作業】
1) 上のスキーマに厳密に従い、このセッションの中身を高品質に作る（英文はネイティブ品質、正解は厳密、解説は丁寧）。
2) 完成したJSONを Write ツールで次の絶対パスに保存する（ファイルの中身はJSONのみ・前後に説明文を書かない）:
   ${path}
3) 保存後、Bashで以下を実行して自己検証し、失敗したら直して再保存する:
   python3 -c "import json; d=json.load(open('${path}')); print('OK ${s.key}', {k:len(d.get(k,[])) for k in (${s.kind==='grammar'?"'kiso','hyojun','nyushi'":"'questions','vocab','points'"})})"
4) 返答は次の1行のみ: 「${s.key} DONE <上のprint結果>」

注意: 返答テキストはワークフローの戻り値であり人間向けメッセージではない。余計な散文は書かず、指定の1行だけ返すこと。`
  const out = await agent(prompt, { label: `gen:${s.key}`, phase: 'Generate' })
  return { key: s.key, kind: s.kind, level: s.level, out: (out || '').slice(-200) }
}))

return { total: SESSIONS.length, results: results.filter(Boolean) }
