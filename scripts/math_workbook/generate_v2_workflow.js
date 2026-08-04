export const meta = {
  name: 'math-v2-generate',
  description: '数IA/IIB 第2集(図形強化)を分野別に新規作問(前集と重複なし・図形はSVG図つき・sympy検算付き)、各分野を敵対的検証',
  phases: [
    { title: 'Generate', detail: '分野ごとに新問+図(SVG)+検算を作る' },
    { title: 'Verify', detail: '分野ごとに答え・図・重複を敵対的に検証' },
  ],
}

const DIR = '/Users/adachishouhei/ai-juku-system/scripts/math_workbook'

const LATEX = `
【数式=教科書準拠のインライン LaTeX($...$)】日本語の地の文は$の外。日本語を$内に絶対入れない(斜体化する)。
- ベクトル \\vec{a} / \\overrightarrow{AB} / |\\vec{a}| / \\vec{a}\\cdot\\vec{b}
- 分数は \\dfrac{}{} (組分数)、根号は \\sqrt{...}、指数 ^{}、下付 _{}
- 積分 \\displaystyle\\int_a^b f(x)\\,dx、総和 \\displaystyle\\sum_{k=1}^{n}、補集合 \\overline{A\\cup B}
- 順列組合せ {}_{n}\\mathrm{P}_{r} / {}_{n}\\mathrm{C}_{r}、不等号 \\leqq \\geqq、度 30^\\circ、θπαβ=\\theta\\pi\\alpha\\beta
- 「よって(hence)」を→で書かない(ベクトルの矢印と衝突)。日本語「よって」を使う。
`

const FIG = `
【図(SVG)の作り方】図が有効な問題には "figure" に自己完結の <svg>...</svg> 文字列を入れる(丸ごと生で埋め込まれる)。
- viewBox は "0 0 W H"(W≤190, H≤150目安)。<script>や外部参照は禁止。属性は全てインライン。
- 主図形: stroke="#1f3a5f" stroke-width="1.5"、多角形の薄い塗り fill="#eef2f7"。問われている要素は stroke="#c8492e" で強調。
- ラベル: <text x=".." y=".." font-size="12">A</text> のように頂点(A,B,C,O,P)・長さ(3)・角(60°)・座標を頂点の少し外に置く。★答え(未知数の値)は図に書かない。
- 直角は小さな正方形マーク、等辺は等分線( tick )で示す。座標問題は x,y 軸(矢印付き)と原点O、直線/円/領域を描く。ベクトルは矢じり付きの線。
- 図は厳密な縮尺でなくてよいが、位置関係・ラベルは正しく。
例(直角三角形 ∠A=90, AB=3, AC=4):
<svg viewBox="0 0 170 140" xmlns="http://www.w3.org/2000/svg"><polygon points="28,116 150,116 28,28" fill="#eef2f7" stroke="#1f3a5f" stroke-width="1.6"/><rect x="28" y="102" width="14" height="14" fill="none" stroke="#1f3a5f" stroke-width="1.1"/><text x="14" y="122" font-size="13">A</text><text x="152" y="122" font-size="13">B</text><text x="14" y="26" font-size="13">C</text><text x="84" y="132" font-size="12">3</text><text x="10" y="76" font-size="12">4</text></svg>
`

const CHK = `
【検算 chk】各問に、答えを sympy で独立に再計算し True を返す Python の lambda ソース文字列 "chk" を必ず付ける。
- 使える名前: import sympy as sp; 記号 x,y,z,a,b,c,d,m,n,k,t,r,s,theta,alpha,beta(全て real); ヘルパ EQ(u,v)=展開一致, NUM(u,v)=数値一致, SOLR(expr,var=x)=実数解集合, SOLC=複素解集合, C(n,r), P(n,r); Interval, FiniteSet, Union, oo, pi, sqrt, Rational as R, sin,cos,tan,log,diff,integrate,binomial。
- ★答えを書き写すだけの自己参照は禁止。問題の条件から値/解集合を導く。bool型を返す(sympyのBool は bool(...) で包む)。
`

const SCHEMA = {
  type: 'object', additionalProperties: false, required: ['unit_name', 'problems'],
  properties: {
    unit_name: { type: 'string' },
    problems: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        required: ['group', 'level', 'type', 'stem', 'answer', 'explanation', 'chk'],
        properties: {
          group: { type: 'string' },
          level: { type: 'string', enum: ['basic', 'standard', 'advanced'] },
          type: { type: 'string', enum: ['short', 'mc'] },
          stem: { type: 'string' }, answer: { type: 'string' }, explanation: { type: 'string' },
          choices: { type: ['array', 'null'], items: { type: 'string' } },
          answer_index: { type: ['integer', 'null'] },
          figure: { type: ['string', 'null'] },
          chk: { type: 'string' },
        },
      },
    },
  },
}

// 分野設定: [book, index, name, count, figMode, 網羅する小分野]
const U = (book, index, name, count, figMode, topics) => ({ book, index, name, count, figMode, topics })
const TASKS = [
  U('ia', 0, '数と式', 11, 'none', '対称式・3次の展開因数分解・二重根号・整数部分小数部分・絶対値を含む方程式不等式・連立不等式'),
  U('ia', 1, '集合と命題', 10, 'venn', '3集合の要素数(ベン図)・必要十分・対偶逆裏・背理法・ド モルガン'),
  U('ia', 2, '二次関数', 12, 'graph', '頂点平方完成・平行移動・区間の最大最小(軸固定/文字入り)・判別式・二次不等式・解の配置。放物線のグラフ図を数問'),
  U('ia', 3, '図形と計量', 13, 'heavy', '三角比の値と相互関係・正弦定理/余弦定理・面積/ヘロン・内接外接円半径・空間図形(正四面体/直方体)。ほぼ全問に図'),
  U('ia', 4, 'データの分析', 10, 'some', '平均中央値最頻値・四分位/箱ひげ図(図)・分散標準偏差・変量変換・相関係数・仮説検定の考え'),
  U('ia', 5, '場合の数', 10, 'some', '順列組合せ・円順列・重複順列/組合せ・同じものを含む順列・最短経路(格子図)・組分け'),
  U('ia', 6, '確率', 10, 'none', '基本・余事象・独立反復・条件付き・期待値・じゃんけん'),
  U('ia', 7, '図形の性質', 13, 'heavy', '重心内心外心垂心・角の二等分線・中点連結・円周角/接弦定理・方べき・チェバメネラウス・接線。ほぼ全問に図'),
  U('ia', 8, '整数の性質', 10, 'none', '約数個数総和・ユークリッド互除法・一次不定方程式・合同/余り・n進法・平方数条件'),
  U('iib', 0, '式と証明', 10, 'none', '二項定理の係数・恒等式・多項式の除法(商余り)・分数式・相加相乗・等式不等式の証明'),
  U('iib', 1, '複素数と方程式', 10, 'none', '複素数計算・解と係数・対称式・剰余因数定理・高次方程式・共役解'),
  U('iib', 2, '図形と方程式', 13, 'heavy', '2点間/内分外分・直線の方程式・平行垂直・点と直線の距離・円の方程式/接線・2円/円と直線・軌跡・領域と最大最小(線形計画)。座標図を多数'),
  U('iib', 3, '三角関数', 12, 'graph', '弧度法・単位円(図)・加法定理2倍角半角・合成・方程式不等式・y=asin(bθ+c)のグラフ(図)と周期振幅'),
  U('iib', 4, '指数関数・対数関数', 10, 'graph', '指数法則・対数計算/底の変換・方程式不等式・桁数(常用対数)・指数対数のグラフ(図1-2)'),
  U('iib', 5, '微分法', 11, 'graph', '微分係数導関数・接線/法線・極値・区間の最大最小・実数解の個数(定数分離)・外部からの接線。3次関数の概形図を数問'),
  U('iib', 6, '積分法', 11, 'graph', '不定/定積分・定積分で表された関数・面積(放物線と直線/2曲線)・1/6公式・偶奇。囲む面積の図を数問'),
  U('iib', 7, '数列', 10, 'none', '等差等比・Σ・階差・(等差)×(等比)の和・漸化式・数学的帰納法・群数列'),
  U('iib', 8, 'ベクトル', 13, 'heavy', '成分/大きさ・内積/なす角・平行垂直条件・内分点/位置ベクトル・分点と交点(1次独立)・空間ベクトル/なす角・図形への応用。ほぼ全問に図'),
  U('iib', 9, '統計的な推測', 10, 'some', '確率変数の期待値分散・二項分布・正規分布(標準化/正規分布曲線図)・標本平均・信頼区間・仮説検定'),
]

const figHint = (m) => ({
  none: '図は基本不要(必要な問題のみ figure を付ける)。',
  some: '該当する小分野(ベン図/箱ひげ図/経路図/正規分布曲線など)には figure を付ける。',
  venn: '集合の問題にはベン図の figure を付ける。',
  graph: '関数のグラフ・単位円・面積など、図が理解を助ける問題の半数程度に figure を付ける。',
  heavy: '図形問題なので原則すべての問題に figure(三角形/円/座標/立体)を付ける。',
})[m]

log(`第2集 生成: ${TASKS.length}分野`)

const results = await pipeline(
  TASKS,
  (task) => agent(
    `あなたは高校数学教科書の作問・組版の専門家です。「数学${task.book === 'ia' ? 'I・A' : 'II・B'}」の分野「${task.name}」について、教科書準拠の新しい問題を ${task.count} 問つくってください(基礎→標準→発展をバランス良く)。\n\n` +
    `★重複回避: JSONファイル ${DIR}/v1_stems_${task.book}.json を Read し、その中の分野「${task.name}」の stems(前集の問題)と「実質的に同じ問題」を作らないこと(数値・設定を変え、別テーマも入れる)。\n` +
    `★網羅する小分野: ${task.topics}。\n` +
    `★図: ${figHint(task.figMode)}\n${FIG}\n${LATEX}\n${CHK}\n\n` +
    `難易度ラベルは実態に合わせる。返すのは構造化データのみ(problems 配列)。`,
    { label: `gen:${task.book}:${task.name}`, phase: 'Generate', schema: SCHEMA, effort: 'high' }
  ),
  (gen, task) => agent(
    `あなたは厳格な数学校閲者です。分野「${task.name}」(数学${task.book === 'ia' ? 'I・A' : 'II・B'})の新規作問を敵対的に検証し、問題があれば直した最終版を返してください。\n\n` +
    `作問結果:\n${JSON.stringify(gen)}\n\n` +
    `チェック:\n` +
    `1. 各問を自分で一から解き、answer と一致するか(sympyをBashで使ってよい)。ill-posed/条件不足/範囲不整合/選択肢と正解のズレを正す。\n` +
    `2. chk が自己参照でなく条件から答えを再計算しているか。構文と利用可能な記号/ヘルパのみか(${CHK})。\n` +
    `3. LaTeX妥当性: $...$ が閉じ、ベクトル上矢印/組分数/√被覆/∫Σ上下限が正しく、日本語が$の中に入っていないか。\n` +
    `4. figure(SVG): 構文が妥当で(閉じタグ・属性)、図の位置関係とラベルが問題文と整合し、★答え(未知数)が図に露出していないか。おかしければ figure を修正。図が不要なのに付いていたら外す。\n` +
    `5. 前集との重複疑い(${DIR}/v1_stems_${task.book}.json を参照)や、この分野内の重複を排除。\n` +
    `6. 難易度ラベルの妥当性。\n\n` +
    `直した最終版を同じスキーマ(unit_name, problems)で返す。自力計算に基づくこと。`,
    { label: `vfy:${task.book}:${task.name}`, phase: 'Verify', schema: SCHEMA, effort: 'high' }
  )
)

const out = results.map((r, i) => r ? { book: TASKS[i].book, unitIndex: TASKS[i].index, unitName: TASKS[i].name, tag: '', ...r } : null)
return out.filter(Boolean)
