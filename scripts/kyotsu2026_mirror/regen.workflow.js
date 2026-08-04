export const meta = {
  name: 'kyotsu2026-regen',
  description: '共通テスト2026類似問題: 未完8パートの作問と英語第4-5問のマーク番号修正',
  phases: [
    { title: 'Create', detail: '未完8パートを仕様書から作問+自己検証+レンダリング確認' },
    { title: 'FixMarks', detail: '英語第4-5問のマーク番号を14-17/18-23へ修正' },
  ],
}

const BASE = '/Users/adachishouhei/ai-juku-system/scripts/kyotsu2026_mirror'
const SPEC = `${BASE}/spec`
const CONTENT = `${BASE}/content`
const CHECK = `${BASE}/build/check_part.py`

const STATUS = {
  type: 'object',
  additionalProperties: false,
  required: ['part', 'file_written', 'check_ok', 'verify_pass', 'summary'],
  properties: {
    part: { type: 'string' },
    file_written: { type: 'boolean', description: 'content/<part>.py を書き終えたか' },
    check_ok: { type: 'boolean', description: 'check_part.py が CHECK OK & bad_glyphs=0 か' },
    verify_pass: { type: 'boolean', description: '数学=verify_<part>.py 全pass / 語学=全設問を自力再解答して一意に解けた' },
    sections: { type: 'string', description: '生成した大問番号(例 "1,2")' },
    marks_or_slots: { type: 'string', description: 'マーク番号範囲またはスロット文字の要約' },
    answer_distribution: { type: 'string', description: '正解位置の分布(偏り確認用)' },
    summary: { type: 'string', description: '3-5行の要約(工夫点・残懸念)' },
  },
}

const PREAMBLE = (key, vertical) => `あなたは大学入学共通テストの熟練作問者です。2026年共通テストの実物仕様に「そっくり(同一形式・同一難易度・マーク数/配点一致)」なオリジナル類似問題を作ります。

必ずこの順で読むこと:
1. ${BASE}/SCHEMA.md — 出力フォーマット(${vertical ? '縦書きunits' : '横書きparts/blocks'})とコンポーネント仕様
2. 下記の該当spec(実物のブループリント=正)

出力ファイル: ${CONTENT}/${key}.py に SECTIONS と ANS_SECTIONS を定義。
★同名の既存ファイルがあれば「途中で力尽きた部分書きの残骸」なので中身は無視して完全に上書きせよ。
★LaTeXは raw string (r"...") で書く。`

const CHECKGATE = (key, vertical) => `

品質ゲート(全て必須・省略不可):
${vertical
  ? `- 全設問を自分で本文に戻って解き直し、正解が一意に定まることを確認(特に「適当でないもの」系は残り選択肢が全て妥当か点検)。`
  : `- ${key.startsWith('math') ? `${CONTENT}/verify_${key}.py を書き、全マークスロットの値を sympy / 全数列挙 / erf など**独立な計算**で導出して assert。実行して全pass させること。` : `全設問を素材に戻って解き直し、正解の根拠が本文に明示され一意に定まることを確認(整序・組合せは全列挙で唯一解を検証)。`}`}
- 正解位置(①〜/選択式スロット)を偏らせない(同一番号の3連続禁止、全体で概ね均等)。
- \`python3 ${CHECK} ${CONTENT}/${key}.py${vertical ? ' --vertical' : ''}\` を実行し **CHECK OK / bad_glyphs=0** を確認。
- ANS_SECTIONS の kai に生徒向け解説(正解根拠+誤答の切り方${key.startsWith('math') ? '、途中式は {"t":"m"}' : ''})。

完了したら StructuredOutput で status を返す(check_ok と verify_pass は実際に実行した結果を正直に。失敗したら false と理由)。`

const PARTS = [
  {
    key: 'math1a_a', vertical: false, phase: 'Create',
    task: `対象: 数学ⅠA 第1問(no=1 配点30)・第2問(no=2 配点30)。
spec: ${SPEC}/math1a_p01-14.md(第1問全部+第2問前半)と ${SPEC}/math1a_p15-28.md(第2問データ分析後半)。
第1問〔1〕集合と命題(述語↔集合の包含・共通解答群10択繰返し可+数値スロット)、〔2〕図形と計量(面積公式の導出を選択で穴埋め→円と接線に適用・桁数漸増)。
第2問〔1〕2次関数(太郎花子の会話+「条件」角丸枠→関数決定と非一意性の考察・順不同スロット)、〔2〕データの分析(1.5×IQRの外れ値定義枠・競技記録28人分の実データ風・散布図2枚+箱ひげ図28本+2×2分割表+相関係数10択+正誤4択)。
図(散布図・箱ひげ図28本)はモジュール内Pythonでデータから計算してSVG生成(viewBox・軸・目盛り・stroke #333・font 10-12)。`,
  },
  {
    key: 'math1a_b', vertical: false, phase: 'Create',
    task: `対象: 数学ⅠA 第3問(no=3 配点20)・第4問(no=4 配点20)。
spec: ${SPEC}/math1a_p15-28.md。
第3問 図形の性質: 二等辺三角形+内心/重心・角の二等分線・方べきの定理→「仮定」枠2つで空間(四面体の体積比較)へ展開→大小比較の選択で締め。平面図+空間図のSVGを幾何的に正確な座標で生成。
第4問 場合の数・確率: 勝率が非対称な対戦ゲーム+ルール明示の角丸枠+星取表(table)複数形態・n人版とm人版の確率比較→最後は2〜3択の大小比較。確率は必ず厳密分数で。`,
  },
  {
    key: 'math2bc_a', vertical: false, phase: 'Create',
    task: `対象: 数学ⅡBC 第1問(no=1 配点15 必答)・第2問(no=2 配点15 必答)。
spec: ${SPEC}/math2bc_p01-16.md。
第1問 図形と方程式: 2円の束 S±L=0(中心・半径・中心間距離の数値マーク)→絶対値入り不等式の領域: 帰属2択×複数・2交点を通る直線の論理選択・**領域9図の共通解答群**(3×3グリッドで9枚のSVGを1ページに)。9図はモジュール内Pythonで系統生成(塗り領域 fill-opacity 0.35、円・直線は正確な座標)。正解の図がスロット解と整合することを定義点代入で自己確認。
第2問 三角関数: 和積公式の導出穴埋め(8択×3)→位相をずらした2項和の最大値→グラフ描画ソフト画面風の図+太郎花子会話(破線枠)→3項和で係数(2cos a+1)構造の発見→係数が負になる仕掛けで最大値再考(10択)。`,
  },
  {
    key: 'math2bc_b', vertical: false, phase: 'Create',
    task: `対象: 数学ⅡBC 第3問(no=3 配点22 必答)・第4問(no=4 配点16 選択 optional:"選択問題")。
spec: ${SPEC}/math2bc_p17-31.md。
第3問 微分積分: 3次関数 f(x)=(1/3)x³+…+k 型: 導関数6択→極値(x数値・値はk込み10択)→k=0/k>0のグラフ概形6図選択→面積等分条件(範囲10択・積分等式4択・負号込み分数マーク)。(2)条件(a)(b)(c)の3段絞り込みで8図→3つ→2つ→1つ(順不同スロット)。概形6図・8図はモジュール内Pythonで3次曲線の実座標をポリライン生成。
第4問 数列: 階差数列の定義提示→基本計算→「発想」枠+太郎会話: (an+b)·rⁿ 型の和を cₙ=(pn+q)·rⁿ 推測で解く(1次結合8択+負号数値)→花子会話で2次式版へ型転移(10択)。Σ上限にスロットを埋める組版は避け本文かtexで表現。積分・数列和はsympyで厳密計算して検証。`,
  },
  {
    key: 'math2bc_c', vertical: false, phase: 'Create',
    task: `対象: 数学ⅡBC 第5問(no=5 配点16)・第6問(no=6 配点16)・第7問(no=7 配点16)いずれも選択(optional:"選択問題")。
spec: ${SPEC}/math2bc_p17-31.md(第5問前半)と ${SPEC}/math2bc_p32-46.md(第5問後半+正規分布表+第6問+第7問)。
第5問 統計的な推測: 試験(満点・合格点)→正規分布の標準化6択+確率8択→ベルヌーイ変数の表+E/V6択→母比率の片側検定(√の近似値を本文指定)→「同比率でも標本サイズで棄却されない」構図の考察。**大問末尾に {"t":"pagebreak"} の後、正規分布表を {"t":"table"} で** (z=0.00〜3.59、行=z₀ 0.0-3.5・列=0.00-0.09、値は math.erf で生成)。本文で使う値と表を一致させる。
第6問 ベクトル: 正六角形の頂点系で MP=aMA+bMB+cMC 型・全スロット選択式(係数10択・条件9択)・(3)直線の通過6択+**領域図6択**(SVG6枚をコード生成)。
第7問 複素数平面: w=z+1/z (ジューコフスキー型)の軌跡: 数値マーク+cos/sin対10択+線分/山型図6択+楕円方程式6択+シフト版の**楕円図8択**(中心±×縦横×大小のSVG8枚)。
検定の棄却判定は臨界値との数値比較で検証。`,
  },
  {
    key: 'english_c', vertical: false, phase: 'Create',
    task: `対象: 英語リーディング 第6問(no=6 配点12 マーク24-31)・第7問(no=7 配点16 マーク32-37)・第8問(no=8 配点17 マーク38-44)。
spec: ${SPEC}/english_p21-39.md(マーク番号割当はspecに厳密に従う)。
第6問(750-800語): 額縁構造の創作物語+作中の手書き風メモ(.hnote+.handw)→Story Outline完成(.outline): 2 of 5順不同+4 of 5時系列整序(ダミー=額縁部の出来事)+抽象化4択×2。
第7問(650-700語): 科学的論説→**プレゼンスライド6枚(2×3グリッド .slides)**完成+生徒カード4枚をTipsに照合する応用6択(組合せC(4,2)を全列挙で検証)。
第8問(Source A論説約150語+Source B棒グラフ): エッセイ執筆プロセス型(Step1-3)。意見5本(賛2/反2/条件付1)→POSITIONメモ完答(40-42の3枠連鎖)→アウトライン完成→**棒グラフSVG(3群×3特徴、境界値トラップ)**をコード生成。
語数はspec推定±10%。整序・組合せ・順不同は全列挙で唯一解を検証。kaiは日本語解説。`,
  },
  {
    key: 'kokugo_a', vertical: true, phase: 'Create',
    task: `対象: 国語 第1問 評論(no=1 配点45 マーク1-10)・第3問 実用文(no=3 配点20 マーク18-22)。本文は完全オリジナル(著作権のため実在文章の流用・改変は厳禁)。
spec: ${SPEC}/kokugo_p01-17.md(第1問)、${SPEC}/kokugo_p18-34.md と ${SPEC}/kokugo_p35-51.md(第3問)。
第1問: 随筆的評論 約3,100字(芸術/文化/社会論系)・(注)6項・傍線A〜E。問1=漢字(傍線部と同じ漢字を含む4択×5小問・番号1-5)、問2〜6=内容説明/理由/筆者の考えの4択(番号6-10)。選択肢は開始句・結び句を揃えた平行構造+誤答3類型(すり替え/過度の一般化/本文にない因果)。
第3問: Mさんの下書き【文章】(段落番号1-4・空欄X)+資料Ⅰ(インタビュー)+資料Ⅱ(別テキスト抜粋)+資料Ⅲ(モデル図)。横組み資料は {"t":"hframe"} で埋め込む。問1=傍線部の具体化修正(18)、問2=波線a〜dから削除箇所選択(19)、問3(i)=特徴比較の誤り2つ選択6択(20・21順不同)+(ii)=分析と方針4択(22)。
本文中の数字は漢数字。傍線は <lA>…</lA>。**行数引用型の選択肢は使わない**。小問配点はANS用に割振り合計45/20に一致。`,
  },
  {
    key: 'kokugo_c', vertical: true, phase: 'Create',
    task: `対象: 国語 第4問 古文(no=4 配点45 マーク23-29)・第5問 漢文(no=5 配点45 マーク30-37)。本文は完全オリジナル(実在古典の本文流用禁止・文体語彙は時代相応に)。
spec: ${SPEC}/kokugo_p35-51.md。
第4問 古文: 平安〜中世の物語風 約1,000-1,100字(擬古文として係り結び・敬語・助動詞接続が文法的に正しいこと)。段落番号1-3・(注)14項・人物関係図({"t":"hframe"}で簡易図)。問1=解釈3問(23-25各4択・語彙×文法2軸の誤肢)、問2=波線a〜dの文法+内容(26)、問3・問4=段落指定の内容説明(27=4択・28=5択)、問5=後日談の会話ボックス×本文照合(29・5択)。
第5問 漢文: 日本漢文風の詩論・オリジナル白文 約160字(漢文として文法的に正しく、訓点=レ点/一二三点/上中下点を {"t":"kanbun"} rows で正確に付す。送り仮名は歴史的仮名遣いカタカナ)。(注)11項。問1=語意2問(30・31)、問2=部分否定の説明(32)、問3=返り点+書き下しの組合せ5択(33)、問4=「不亦〜乎」型句形の解釈(34)、問5=行動の理由(35)、問6=比喩の内容説明(36)、問7=同著者の別文章【資料】(白文約45字)と本文の統合4択(37)。傍線Bのみ白文にする等specの白文/訓点使い分けを踏襲。
古文の文法と漢文の訓点(返り点整合・書き下し一致)を一字ずつ検査。問3の組合せ5択は返り点と書き下しが矛盾なく唯一解。kaiは全訳+句法/文法解説。本文の数字は漢数字。`,
  },
]

phase('Create')
const results = await parallel(
  PARTS.map(p => () =>
    agent(PREAMBLE(p.key, p.vertical) + '\n\n' + p.task + CHECKGATE(p.key, p.vertical),
      { label: `create:${p.key}`, phase: 'Create', schema: STATUS })
  )
)

phase('FixMarks')
const fix = await agent(
  `${CONTENT}/english_b.py は完成済みだがマーク番号が誤っている。実物specでは 第4問=解答番号14〜17(4枠)、第5問=解答番号18〜23(6枠)。現状は 第4問=13〜16、第5問=17〜23 になっている(第3問が8〜13を使うため13が衝突し、全体が1つずれている)。

必読: ${BASE}/SCHEMA.md と ${SPEC}/english_p01-20.md(第4問・第5問の解答番号割当)。

作業:
1. ${CONTENT}/english_b.py を読み、第4問の設問(qの no と stem 中の {Q}/[番号]表記)と ANS_SECTIONS の qno を 14,15,16,17 に、第5問を 18,19,20,21,22,23 に振り直す。順不同2枠は 22・23。
2. マーク番号以外の本文・選択肢・正解は変えない(番号のみのリナンバー)。ANS_SECTIONS の points 合計が 第4問=12・第5問=16 のままであることを確認。
3. \`python3 ${CHECK} ${CONTENT}/english_b.py\` で CHECK OK / bad_glyphs=0 を確認。
4. 各設問の正解が本文根拠で一意に解けることも一通り再確認。

StructuredOutput で status を返す(part="english_b")。`,
  { label: 'fix:english_b', phase: 'FixMarks', schema: STATUS })

return { created: results.filter(Boolean), english_b_fix: fix }
