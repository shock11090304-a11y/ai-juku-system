# 英検準1級 単語テスト 作問ルールブック（第11〜20回）

1エントリ = (word, pos, gloss, (誤答1, 誤答2, 誤答3), usage_en, usage_ja, note)
pos は 動 / 名 / 形 / 副 / 熟 のいずれか1文字。

## 最重要（このルールは実際に踏んだ事故から作られている）

生徒は「英単語を読まずに、日本語の選択肢の見た目だけで正解を当てられてはいけない」。
過去5世代、次の抜け道が順に生まれた。**あなたの原稿でも必ず起きるので意識して書くこと。**

### R1 長さをそろえる（最重要）
正解の語義と誤答3つの**文字数を±2字以内**にそろえる。
（数えるときは 〜 （ ） ・ ／ 、 。 を除く）
- 悪い例: 正解「厳格な」(3) に対し誤答「曲がらず硬直した」(8)「活気にあふれた」(7)
  → 最短を選ぶだけで当たってしまう。実測で34.5%取られた。
- 良い例: 正解「厳格な」(3) / 誤答「雑な」(2)「活発な」(3)「硬直した」(4)

### R2 調子（レジスタ）をそろえる
正解の語義は抽象的・改まった語になる。**誤答も同じ調子にする。**
- 悪い例: 正解「〜を骨抜きにする」に対し誤答「〜に水をやる」「〜を洗い流す」「〜を水中に沈める」
  → 日常の具体的動作ばかりで、抽象語である正解が一目で浮く。
- **物理的な具体物**（洗剤・真珠・打楽器・月曜日・弦楽器・胞子・遺言・鉛筆…）を指す誤答は
  **1問に最大1本**。綴りの混同を誘う狙い（deterrent/detergent など）があるときだけ1本置いてよい。

### R3 記号を正解肢に集めない
gloss の**第1義がそのまま選択肢に印字される**。第1義に丸カッコ（）と中黒・を**使わない**。
限定が要るなら第2義以降に回す。例: gloss「〜を実施する、（政策などを）実行に移す」→ 印字は「〜を実施する」

### R4 その語の別の正しい語義を誤答に入れない（正解が2つになる事故）
多義語は特に注意。例: sanction は「制裁」と「認可」の両方を持つので、片方を誤答にしてはいけない。

### R5 使ってはいけない書き方
- 極端強調: 完全な／きわめて／到底／全面的／誰の目にも／揺るぎない（19本すべて誤答になり tell になった）
- 同じ回の中で同じ誤答を2回使う
- 正解と誤答をあからさまな対義ペアにするのを毎問やる（2肢が対義だと答えがそこだと分かる。回に数問まで）

## その他

### R6 usage_en / usage_ja は gloss の第1義と対応させる
実在するコロケーションにする。★語義の順番を決めたら用例を読み直すこと。
（実例: gloss を「〜する気にさせる」に直したのに用例が "induce sleep（眠気を誘う）" のまま残った）

### R7 note に他の見出し語を書かない（解答漏洩）
note と usage_en/usage_ja に、**別の回の見出し語（下の禁止リスト）を書いてはいけない**。
派生語であってもリストに載っていれば書かない。
（実例: deter のメモ「名 deterrent」が、第8回の見出し語 deterrent の答えを先出ししていた）
note は派生語・混同注意・反意語・語源イメージなどを**1行**で。無理に書かなくてよい。

### R8 レベル
英検準1級の**中核**。2級以下で出る易しい語（explain, increase, decide 等）の語義そのままは避け、
かといって1級・専門語に振らない。誤答も準1級の生徒が意味を取れる日本語にする。

## 禁止リスト（note / usage に書いてはいけない見出し語・全400語）
★このリストは content.py から生成すること。手で写すと差し替えのたびにずれる
（実際に inference / account for the bulk of / carry out / get along with の4語がずれていた）。
  alleviate / deteriorate / mitigate / advocate / undermine / comply / exacerbate / deter
  allocate / scrutiny / discrepancy / incentive / backlash / prerequisite / plight / surge
  iron out / weed out / rule out / come down with / plausible / meticulous / susceptible / inevitable
  lucrative / prevalent / redundant / tentative / resilient / ambiguous / compelling / inadvertently
  unanimously / sparingly / presumably / profoundly / get away with / cut back on / at odds with / on the verge of
  implement / facilitate / foster / hamper / entail / impair / incur / inhibit
  deploy / curb / constraint / disparity / consensus / hierarchy / deficit / initiative
  contend with / in the wake of / stem from / take a toll on / eradicate / suppress / refute / endorse
  streamline / offset / thrive / undertake / speculate / deplete / aftermath / threshold
  momentum / setback / sanction / proponent / crack down on / shed light on / live up to / phase out
  accumulate / compensate / discern / denounce / reinforce / retain / trigger / verify
  contaminate / dwindle / anomaly / rationale / repercussion / outbreak / surplus / vicinity
  account for / abide by / single out / wear off / adverse / arbitrary / compulsory / detrimental
  eligible / feasible / imminent / indispensable / obsolete / rigorous / subtle / versatile
  vulnerable / conversely / drastically / invariably / keep abreast of / make headway / opt for / water down
  attribute / bolster / confine / delegate / disclose / enforce / induce / prohibit
  replicate / revoke / apprehension / bias / commodity / negligence / skepticism / upheaval
  fall through / gloss over / pin down / usher in / alienate / ascertain / condone / deem
  emulate / instill / relinquish / resent / sustain / wane / adversity / allegation
  deterrent / downturn / quota / testimony / bank on / lash out at / mull over / ramp up
  augment / compile / depict / designate / impose / outweigh / penalize / subsidize
  validate / yield / implication / infrastructure / integrity / peril / remnant / stagnation
  dwell on / fend off / sift through / wind up doing / articulate / constitute / cultivate / lure
  perceive / supplement / terminate / abundant / conducive / formidable / impartial / lenient
  mundane / negligible / sporadic / stringent / at the expense of / in tandem with / on a par with / jump the gun
  diminish / escalate / fluctuate / plummet / soar / amplify / intensify / subside
  magnify / stabilize / proliferate / erode / surpass / exceed / curtail / swell
  taper off / level off / fall short of / give rise to / assert / allege / affirm / concede
  dispute / infer / deduce / imply / justify / acknowledge / dismiss / uphold
  condemn / proclaim / testify / contradict / stand by / stand for / back down / go along with
  tackle / cope / execute / administer / oversee / supervise / coordinate / devise
  formulate / commence / pursue / consolidate / prioritize / mobilize / orchestrate / expedite
  follow through on / work out / set out / take on / legislation / jurisdiction / mandate / referendum
  regime / bureaucracy / autonomy / sovereignty / treaty / coalition / statute / amendment
  ballot / census / verdict / welfare / in accordance with / on behalf of / in the face of / subject to
  premise / hypothesis / paradigm / notion / doctrine / ideology / discourse / rhetoric
  fallacy / analogy / connotation / conjecture / paradox / dilemma / criterion / perspective
  in light of / by virtue of / in terms of / with regard to / substantial / considerable / marginal / moderate
  extensive / comprehensive / exhaustive / thorough / ample / meager / sparse / widespread
  pervasive / ubiquitous / staggering / modest / boil down to / add up to / amount to / by and large
  diligent / conscientious / prudent / discreet / candid / blunt / assertive / arrogant
  humble / stubborn / adaptable / complacent / indifferent / reluctant / cynical / ruthless
  look down on / look up to / put up with / take after / literal / discrete / principal / sensible
  economical / historic / continual / respective / industrious / considerate / comprehensible / momentous
  alternate / virtual / nominal / apparent / on the contrary / for the sake of / in the long run / at the mercy of
  conform / adhere / coincide / correspond / resemble / distinguish / integrate / incorporate
  encompass / comprise / denote / exemplify / illustrate / portray / characterize / embody
  consist of / result in / derive from / cater to / undergo / withstand / endure / tolerate
  persist / prevail / succumb / forfeit / preserve / conserve / safeguard / restore
  revive / replenish / salvage / thwart / hold out / hang on to / ride out / come to terms with

## 出力形式（JSON）
[
 {"word":"diminish","pos":"動","gloss":"減少する、〜を減らす",
  "distractors":["急増する","停滞する","分散する"],
  "usage_en":"diminish over time","usage_ja":"時とともに減少する","note":"名 diminution"},
 ...
]
