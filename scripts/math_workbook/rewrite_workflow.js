export const meta = {
  name: 'math-latex-rewrite',
  description: '数IA/IIBの数式を教科書準拠LaTeXに再記述し、各分野に山場の発展問題を追加(sympy検算付き)、各分野を敵対的検証',
  phases: [
    { title: 'Rewrite', detail: '分野ごとにLaTeX変換+新規発展問題を生成' },
    { title: 'Verify', detail: '分野ごとに忠実性・新規問題の正しさを敵対的検証' },
  ],
}

const IA_PATH = '/Users/adachishouhei/ai-juku-system/scripts/math_workbook/ia_display.json'
const IIB_PATH = '/Users/adachishouhei/ai-juku-system/scripts/math_workbook/iib_display.json'

const RULES = `
【LaTeX変換ルール(教科書=数研/東京書籍 準拠)】
既存問題の stem/answer/explanation/choices の中の「数式部分だけ」をインライン $...$ の LaTeX に変換する。日本語の地の文は $ の外にそのまま残す。★数学的な値は絶対に変えない(これは記号の付け替えであって解き直しではない)。
- 指数: ^{...} / ^2 → そのまま LaTeX の ^{...} / ^2
- 下付き: _{...} / _n → _{...} / _n
- ベクトル: a→ → \\vec{a} , AB→ → \\overrightarrow{AB} , |a→| → |\\vec{a}| , a→·b→ → \\vec{a}\\cdot\\vec{b}
- 分数: 26/3 → \\dfrac{26}{3} , -4/3 → -\\dfrac{4}{3} , (√6+√2)/4 → \\dfrac{\\sqrt6+\\sqrt2}{4} , √3/2 → \\dfrac{\\sqrt3}{2} , x+4/x → x+\\dfrac{4}{x} , n(n+1)/2 → \\dfrac{n(n+1)}{2} , 1/α+1/β → \\dfrac{1}{\\alpha}+\\dfrac{1}{\\beta}
- 根号: √3 → \\sqrt{3} , √48 → \\sqrt{48} , √(a²+b²) → \\sqrt{a^2+b^2} , 2√5 → 2\\sqrt{5} , 複素数の √3 i → \\sqrt{3}\\,i
- 積分: ∫_0^2 2x dx → \\displaystyle\\int_0^2 2x\\,dx ,  [x²]_0^2 → \\Big[x^2\\Big]_0^2
- 総和: Σ_{k=1}^{n} k → \\displaystyle\\sum_{k=1}^{n} k
- 集合の補集合: 「(A∪B) の上線」「Aの補集合」→ \\overline{A\\cup B} , \\overline{A}
- 順列組合せ: _{5}P_{3} → {}_{5}\\mathrm{P}_{3} , _{7}C_{3} → {}_{7}\\mathrm{C}_{3}
- 不等号: ≦ → \\leqq , ≧ → \\geqq (< > はそのまま)
- ギリシャ/記号: θ→\\theta π→\\pi α→\\alpha β→\\beta , 30° → 30^\\circ , ± → \\pm , 掛算の · → \\cdot , × → \\times
- 集合演算: ∪→\\cup ∩→\\cap ⊂→\\subset ∈→\\in , ⇔→\\iff , ⇒→\\Rightarrow
- ★重要: 「よって/ゆえに」の意味で使われている矢印 →(例: …=1/√2 → θ=45°) は、ベクトルの矢印と衝突するので、日本語「よって」に置き換える($ の外)。ベクトルの → だけ \\vec/\\overrightarrow にする。
- 選択肢の丸数字 ①②③④ は $ の外(そのまま)。座標 (2,3) は $(2,3)$ でよい。
- KaTeXで確実に描画できる要素だけ使う。壊れる長い装飾は避け、素直に書く。
`

const CHK_RULES = `
【新規問題の chk(検算)ルール】
各新規問題に、答えを sympy で「独立に再計算」して True を返す Python の lambda ソース文字列 "chk" を必ず付ける。
- 利用可能: import sympy as sp; 記号 x,y,z,a,b,c,d,m,n,k,t,r,s,theta,alpha,beta (すべて real=True); ヘルパ EQ(u,v)=展開して一致, NUM(u,v)=数値一致, SOLR(expr,var=x)=実数解集合(solveset), SOLC=複素解集合, C(n,r)=組合せ, P(n,r)=順列, Interval, FiniteSet, Union, oo, pi, sqrt, Rational as R, sin,cos,tan,log,diff,integrate,binomial。
- ★答えを文字列で書き写すだけの自己参照チェックは禁止。必ず問題の条件から値/解集合を導く形にする。
  例(解の配置): "lambda: SOLR(sp.And(m**2-m-2>0, m>0, m+2>0), m) == Interval.open(2, oo)" のように条件から範囲を出す。難しければ、境界値と代表点で場合分けを検証する形でよい。
- bool型を返すこと(sympyのBooleanTrueは bool(...) で包む)。
`

const SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['unit_name', 'rewritten', 'new_problems'],
  properties: {
    unit_name: { type: 'string' },
    rewritten: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        required: ['idx', 'stem', 'answer', 'explanation'],
        properties: {
          idx: { type: 'integer' },
          stem: { type: 'string' }, answer: { type: 'string' }, explanation: { type: 'string' },
          choices: { type: ['array', 'null'], items: { type: 'string' } },
        },
      },
    },
    new_problems: {
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
          chk: { type: 'string' },
        },
      },
    },
  },
}

// 追加すべき山場問題(coverage レビューより)。分野名キー。
const ADD = {
  ia: {
    '数と式': ['絶対値不等式(例 |2x-1|<5)を1問', '3次の因数分解(a^3-b^3 型, 例 x^3-8)を1問'],
    '集合と命題': ['[発展]背理法または必要十分条件の総合問題を1問(sympyで検算可能な形に)'],
    '二次関数': ['[発展]解の配置(例 x^2-2mx+m+2=0 が異なる2つの正の解をもつ m の範囲)を1問', '[発展]区間における最大・最小の場合分け(例 0≦x≦2 で y=x^2-2ax の最小値を a で場合分け)を1問'],
    '図形と計量': ['三角比の方程式(例 0°≦θ≦180° で sinθ=√3/2)を1問', '空間図形への応用(例 1辺6の正四面体の体積)を1問'],
    'データの分析': ['箱ひげ図・五数要約(Q1,Q2,Q3,四分位範囲)の読み取り/計算を1問', '2変量データから共分散を実際に計算する問題を1問'],
    '場合の数': ['重複組合せ(例 3種類から7個選ぶ)を1問'],
    '確率': ['期待値[基礎](例 くじ/さいころの目の期待値)を1問', '期待値[標準](例 コイン2枚の表の枚数の期待値)を1問'],
    '図形の性質': ['メネラウスの定理の数値問題を1問(新規)'],
    '整数の性質': ['√(360n) が自然数となる最小の自然数 n など、平方数条件の問題を1問'],
  },
  iib: {
    '式と証明': ['多項式の除法の商と余り(例 x^3+2x^2-x+5 を x+1 で割る)を1問'],
    '複素数と方程式': ['[発展]実数係数方程式の共役な虚数解 or 3次の解と係数の関係を1問'],
    '図形と方程式': ['円上の点における接線の方程式(例 x^2+y^2=5 上の点(1,2))を1問', '[発展]線形計画法(領域における1次式の最大最小)を1問'],
    '三角関数': ['グラフ・周期・振幅(例 y=2sin(2θ-π/3) の周期と最大値)を1問', '半角の公式または積和の公式を用いる問題を1問'],
    '指数関数・対数関数': ['対数不等式(例 log_2(x-1)<3)を1問', '常用対数による桁数(例 2^30 は何桁か, log10 2=0.3010)を1問'],
    '微分法': ['[発展]3次方程式の実数解の個数(定数分離, 例 x^3-3x=a)を1問'],
    '積分法': ['2曲線で囲まれた面積(例 y=x^2 と y=-x^2+2x)を1問'],
    '数列': ['数学的帰納法で示す等式(例 1+3+5+…+(2n-1)=n^2)を1問(chkは複数のnで公式を検証)', '階差数列(例 a_1=1, 階差2n から一般項)を1問'],
    'ベクトル': ['[発展]三角形の内部の交点の位置ベクトル(1次独立な分解)を1問', '空間ベクトルの内積・なす角(例 (1,1,0)と(1,0,1))を1問'],
  },
}

// 18分野のタスクリストを作る
const TASKS = []
for (const book of ['ia', 'iib']) {
  const path = book === 'ia' ? IA_PATH : IIB_PATH
  const names = Object.keys(ADD[book])
  names.forEach((name, i) => {
    TASKS.push({ book, path, unitIndex: i, unitName: name, adds: ADD[book][name] })
  })
}

log(`再組版タスク ${TASKS.length} 分野 (ia+iib) を開始`)

const results = await pipeline(
  TASKS,
  // Stage 1: 変換 + 新規生成
  (task) => agent(
    `あなたは高校数学教科書の組版・作問の専門家です。JSONファイル ${task.path} を Read し、その中の ${task.unitIndex} 番目(0始まり)の分野「${task.unitName}」の problems 配列を対象に、次の2つを行ってください。\n\n` +
    `(1) 既存の各問題の stem / answer / explanation / choices の数式を、下記ルールで教科書準拠のインライン LaTeX($...$)に変換する。idx を保持し、problems と同じ順・同じ件数で返す。日本語はそのまま。値は変えない。\n${RULES}\n\n` +
    `(2) この分野に、以下の「山場」問題を新規作成して new_problems に入れる(各問に独立検算 chk 付き。stem等は最初から上記LaTeXルールで記述):\n- ${task.adds.join('\n- ')}\n${CHK_RULES}\n\n` +
    `難易度ラベルは実態に合わせる(公式代入だけの問題を[発展]にしない)。返すのは構造化データのみ。`,
    { label: `rewrite:${task.book}:${task.unitName}`, phase: 'Rewrite', schema: SCHEMA, effort: 'high' }
  ),
  // Stage 2: 敵対的検証(忠実性 + 新規問題の正しさ)
  (rw, task) => agent(
    `あなたは厳格な数学校閲者です。分野「${task.unitName}」の再組版結果を敵対的に検証し、問題があれば「直した最終版」を返してください。\n\n` +
    `元データ(変換前, 値の正解): JSONファイル ${task.path} の ${task.unitIndex} 番目の分野。必ず Read して照合すること。\n` +
    `再組版結果(検証対象):\n${JSON.stringify(rw)}\n\n` +
    `チェック項目:\n` +
    `1. 忠実性: rewritten の各問が、元データと「数学的に同値」か(LaTeX化で値・符号・範囲が変わっていないか)。idx対応・件数一致。\n` +
    `2. LaTeX妥当性: $...$ が閉じているか、\\vec/\\overrightarrow/\\dfrac/\\sqrt/\\displaystyle\\int/\\displaystyle\\sum/\\overline/{}_n\\mathrm{P}_r/\\leqq 等が正しく、KaTeXで描画できるか。ベクトルは上矢印か。「よって」の→衝突が残っていないか。\n` +
    `2b. 混在チェック: 日本語の地の文が $...$ の中に入っていないか(KaTeXが日本語を斜体英字に化けさせるので厳禁)。数式だけを$で囲むこと。\n` +
    `3. 新規問題の正しさ: new_problems の各問を「あなた自身が一から解いて」answer と一致するか確認。問題文が一意に解けるか。chk が自己参照でなく本当に条件から答えを再計算しているか(そうでなければ chk を書き直す)。難易度ラベルは妥当か。\n` +
    `4. sympy的に chk が実行可能か(構文・利用可能な記号/ヘルパのみ使用: ${CHK_RULES})。\n\n` +
    `見つけた問題は自分で修正し、最終版(rewritten と new_problems)を同じスキーマで返すこと。問題が無ければそのまま返す。憶測でなく Read と自力計算に基づくこと。`,
    { label: `verify:${task.book}:${task.unitName}`, phase: 'Verify', schema: SCHEMA, effort: 'high' }
  )
)

// book/unitIndex を結果に添えて返す
const out = results.map((r, i) => r ? { book: TASKS[i].book, unitIndex: TASKS[i].unitIndex, unitName: TASKS[i].unitName, ...r } : null)
return out.filter(Boolean)
