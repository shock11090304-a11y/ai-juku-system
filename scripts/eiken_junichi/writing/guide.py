# -*- coding: utf-8 -*-
"""① コツと進め方編 の本文 (固定の説明文)。例題の部分は build.py が data/examples.json から組む。

★ここに書く語数の範囲 (要約 60〜70語・意見論述 120〜150語) は check.py の SUMMARY_RANGE / ESSAY_RANGE と
  同じ値にすること (解答例はその範囲で機械検査している)。
"""


def overview():
    return """
<h2 class="sec"><span class="no">1</span>ライティングの全体像</h2>
<table class="t">
<tr><th style="width:17%"></th><th>大問4　要約（Summary）</th><th>大問5　意見論述（Opinion essay）</th></tr>
<tr><th>何をする</th><td>200語程度の英文（3段落）を読み、内容を英語で要約する</td><td>TOPIC（問い）に対して、自分の意見と理由を英語で書く</td></tr>
<tr><th>語数</th><td><b>60〜70語</b></td><td><b>120〜150語</b></td></tr>
<tr><th>条件</th><td>できるだけ<b>自分の言葉で</b>（本文の丸写しはしない）</td><td>POINTS（4つ）から<b>2つ</b>を選んで理由に使う／序論・本論・結論の構成</td></tr>
<tr><th>採点</th><td colspan="2">どちらも<b>内容・構成・語彙・文法</b>の4観点（各4点・16点満点）</td></tr>
<tr><th>時間の目安</th><td>15〜20分</td><td>20〜25分</td></tr>
</table>

<div class="box key"><div class="bh">ライティングは「たった2題で750点」</div>
準1級の一次試験は、リーディング・リスニング・ライティングの3技能がそれぞれ750点満点（英検CSEスコア）。
ライティングは<b>2題だけで、リーディング31問と同じ750点分</b>です。1題の出来が合否を大きく動かすので、
<b>いちばん伸ばしやすく、いちばん落としてはいけない</b>パート。一次試験の合格の目安は3技能の合計で 1792点（満点2250点）です。</div>

<div class="box warn"><div class="bh">0点にしないために</div>
<ul>
<li>要約に<b>自分の意見</b>や<b>本文にない内容</b>を書く → 「要約になっていない」と判断されると0点のことがある</li>
<li>意見論述で<b>TOPIC からずれる</b>（問いに答えていない）→ 0点のことがある</li>
<li>語数は「目安」だが、大きく外れると内容・構成で不利になる。<b>必ず範囲内に収める</b></li>
</ul></div>

<h3 class="sub">筆記90分の使い方（例）</h3>
<table class="t center">
<tr><th>大問1 語彙</th><th>大問4 要約</th><th>大問5 意見論述</th><th>大問2・3 長文</th><th>見直し</th></tr>
<tr><td>10分</td><td>15〜20分</td><td>20〜25分</td><td>35分前後</td><td>数分</td></tr>
</table>
<p>ライティングを最後に回して<b>時間切れで書けない</b>のが、いちばんもったいない失点です。語彙のあとにライティングを片づける順番がおすすめ。
自分に合う順番は、第8週からの過去問演習で決めましょう。</p>
"""


def summary_tips():
    return """
<h2 class="sec"><span class="no">2</span>要約のコツ<small>大問4・60〜70語</small></h2>

<div class="rule"><div class="n">1</div><div><div class="h">まず「段落の役割」をつかむ</div>
準1級の要約は<b>3段落</b>が基本。段落ごとに役割があり、<b>各段落から要点を1つずつ</b>拾えば骨組みが完成します。
<table class="t">
<tr><th>型</th><th>第1段落</th><th>第2段落</th><th>第3段落</th></tr>
<tr><td>型A</td><td>背景・変化</td><td>利点（賛成派）</td><td>欠点・課題（反対派）</td></tr>
<tr><td>型B</td><td>問題</td><td>影響・原因</td><td>対策（とその限界）</td></tr>
<tr><td>型C</td><td>変化・新しい動き</td><td>賛成派の意見</td><td>反対派の意見</td></tr>
</table>
語数の配分の目安は <b>第1段落 15〜20語／第2段落 20〜25語／第3段落 20〜25語</b>。</div></div>

<div class="rule"><div class="n">2</div><div><div class="h">具体例・数字・固有名詞は削って「まとめ語」にする</div>
<span class="en">such as</span> / <span class="en">for example</span> の後ろ、数字、人名・地名は基本的に書きません。いくつかの具体例は<b>1語のまとめ語</b>に置きかえます。<br>
<span class="en">lettuce and herbs</span> → <span class="en"><b>vegetables</b></span>　／　<span class="en">cars, buses, and trains</span> → <span class="en"><b>vehicles</b></span>　／　<span class="en">Tokyo, Osaka, and Nagoya</span> → <span class="en"><b>large cities</b></span></div></div>

<div class="rule"><div class="n">3</div><div><div class="h">言い換え（パラフレーズ）の3つの技</div>
<table class="t">
<tr><th style="width:24%">技</th><th>本文</th><th>要約</th></tr>
<tr><td>① 語をかえる</td><td class="en">hire enough staff</td><td class="en">recruit workers</td></tr>
<tr><td>② 品詞をかえる（文 → 名詞句）</td><td class="en">self-checkout lines often move faster</td><td class="en">shorter waits</td></tr>
<tr><td>③ 構文をかえる</td><td class="en">Because prices rose, people bought less.</td><td class="en">Rising prices led people to buy less.</td></tr>
</table>
<b>専門用語やキーワード</b>（<span class="en">artificial intelligence, climate change</span> など）はそのまま使ってかまいません。言い換えにこだわって<b>意味が変わる方が大きな減点</b>です。</div></div>

<div class="rule"><div class="n">4</div><div><div class="h">つなぎ言葉で「論理の流れ」を見せる</div>
段落どうしの関係を1語で示します。
利点 → 欠点：<span class="en"><b>However,</b></span>　原因 → 結果：<span class="en"><b>As a result, / so / lead to</b></span>　問題 → 対策：<span class="en"><b>To address this, / In response,</b></span>　意見の対立：<span class="en"><b>Supporters say … . However, critics argue …</b></span></div></div>

<div class="rule"><div class="n">5</div><div><div class="h">書いてはいけないもの</div>
自分の意見（<span class="en">I think / I agree</span>）・本文にない情報・<span class="en">This passage says …</span> のような前置き（語数のむだ）。
賛成派・反対派の意見は、<span class="en">Supporters claim that …</span> のように<b>誰の意見か</b>を書く（書かないと自分の意見に見える）。</div></div>

<div class="rule"><div class="n">6</div><div><div class="h">最後に必ず語数を数える</div>
5語ごとに小さく「／」を入れて数えると速い。60語未満・70語超なら直します。本書の語数は「スペースで区切られたまとまり＝1語」で数えています（<span class="en">self-checkout</span> は1語）。</div></div>

<div class="rule"><div class="n">7</div><div><div class="h">15〜20分の使い方</div>
<b>読む</b>：段落ごとに要点に線を引く（5分）→ <b>メモ</b>：日本語で3行（3分）→ <b>書く</b>（8分）→ <b>見直し</b>：語数・主語と動詞・冠詞（2分）</div></div>
"""


def essay_tips():
    return """
<h2 class="sec"><span class="no">3</span>意見論述のコツ<small>大問5・120〜150語</small></h2>

<div class="rule"><div class="n">1</div><div><div class="h">型（テンプレート）を決めておく</div>
毎回ゼロから考えないこと。4段落の型に中身を流し込みます。</div></div>
<div class="tmpl">
<div class="row"><div class="lab"><span class="tag intro">序論</span></div><div class="en">I believe that ＋ TOPIC の文. I have two reasons for this opinion.<br><span class="small muted" style="font-family:'Noto Sans JP',sans-serif">反対なら：I disagree with the idea that ＋ TOPIC の文. ／ I do not think that ＋ TOPIC の文.<br>★ Should … ? 型の TOPIC は肯定文に直して続ける（Should the age be raised? → the age should be raised）</span></div><div class="wc">20語前後</div></div>
<div class="row"><div class="lab"><span class="tag body1">本論1</span></div><div class="en">First, ＋ 理由（POINT ①）. ＋ 説明. ＋ 具体例・結果.</div><div class="wc">45〜55語</div></div>
<div class="row"><div class="lab"><span class="tag body2">本論2</span></div><div class="en">Second, ＋ 理由（POINT ②）. ＋ 説明. ＋ 具体例・結果.</div><div class="wc">45〜55語</div></div>
<div class="row"><div class="lab"><span class="tag concl">結論</span></div><div class="en">For these reasons, I believe that ＋ 立場の言い換え.</div><div class="wc">15〜20語</div></div>
</div>

<div class="rule"><div class="n">2</div><div><div class="h">立場は「書きやすい方」を選ぶ</div>
本当の意見でなくてかまいません。POINTS を見て、<b>説明と具体例が2つすぐ浮かぶ側</b>を選びます（迷うのは2分まで）。</div></div>

<div class="rule"><div class="n">3</div><div><div class="h">POINTS は2つ・1段落に1つ</div>
3つ以上使うと1つあたりが薄くなります。POINT の語はそのまま使っても言い換えてもよい。
同じ POINT が賛成・反対のどちらの理由にもなることが多い（例：<span class="en">Health</span> は「働くと健康を保てる」にも「高齢で働くのは負担」にもなる）。</div></div>

<div class="rule"><div class="n">4</div><div><div class="h">理由は「主張 → 説明 → 具体例・結果」の3段</div>
<span class="ng">✗</span> 理由を1文言って終わり　→　<span class="ok">○</span> なぜそう言えるか（説明）と、例や「その結果どうなるか」まで書く。1段落45〜55語はこの3段で自然に埋まります。</div></div>

<div class="rule"><div class="n">5</div><div><div class="h">社会全体の視点で書く</div>
主語は <span class="en">people / companies / the government / society</span> など。個人の体験談だけで終わらせない。
数字や統計は、不確かなら書かない（<span class="en">many / a growing number of</span> で十分）。</div></div>

<div class="rule"><div class="n">6</div><div><div class="h">最初と最後で立場をぶらさない</div>
結論では序論の立場を<b>別の表現でくり返す</b>だけ。新しい理由は出さない。<span class="en">I partly agree</span> のような中間の立場は避ける。</div></div>

<div class="rule"><div class="n">7</div><div><div class="h">20〜25分の使い方</div>
<b>立場を決めてメモ</b>（5分）→ <b>書く</b>（15分）→ <b>見直し</b>：語数・立場の一貫性・文法（3〜5分）</div></div>
"""


def mistakes():
    rows = [
        ("Because it is convenient.", "This is because it is convenient.", "Because の節だけでは文にならない（主節が必要）"),
        ("People can get many informations.", "People can get a lot of information.", "information は数えられない名詞"),
        ("It makes people to feel stressed.", "It makes people feel stressed.", "make＋人＋動詞の原形"),
        ("The number of elderly people are increasing.", "The number of elderly people is increasing.", "主語は the number（単数）"),
        ("If the government will ban plastic bags, …", "If the government bans plastic bags, …", "条件の if 節では未来のことも現在形"),
        ("I agree this opinion.", "I agree with this opinion.", "agree with＋意見・人"),
        ("We should discuss about this problem.", "We should discuss this problem.", "discuss は他動詞（about は不要）"),
        ("In my opinion, I think that …", "In my opinion, … ／ I think that …", "同じ意味の重複"),
        ("It can't be denied that …", "It cannot be denied that …", "エッセイでは短縮形を使わない"),
        ("For example, smartphones.", "For example, smartphones allow people to …", "For example のあとも完全な文にする"),
        ("kids ／ stuff", "children ／ things", "口語は書き言葉に"),
        ("This is very good.", "This would reduce the burden on parents.", "評価語だけでなく「何にどう良いか」を書く"),
    ]
    trs = "".join(
        f'<tr><td class="en ng">✗ {a}</td><td class="en ok">○ {b}</td><td>{c}</td></tr>' for a, b, c in rows)
    return f"""
<h2 class="sec"><span class="no">4</span>よくあるミス（文法の減点を防ぐ）</h2>
<table class="t"><tr><th style="width:35%">よくある誤り</th><th style="width:37%">正しい形</th><th>ポイント</th></tr>{trs}</table>
"""


def expressions():
    s_rows = [
        ("変化・普及", "have become increasingly common ／ have spread rapidly"),
        ("利点（誰かの主張）", "Supporters argue that … ／ … offers several benefits"),
        ("欠点・反対意見", "However, critics point out that … ／ … also has drawbacks"),
        ("因果", "… has led to … ／ …, which results in … ／ As a result, …"),
        ("対策", "To address this problem, … ／ In response, …"),
        ("対比", "…, while … ／ …, whereas …"),
    ]
    e_rows = [
        ("立場", "I believe that … ／ I disagree with the idea that …"),
        ("理由の予告", "I have two reasons for this opinion. ／ There are two main reasons for my opinion."),
        ("列挙", "First, … Second, … ／ To begin with, … In addition, …"),
        ("具体例", "For example, … ／ …, such as A and B, …"),
        ("結果", "As a result, … ／ This would lead to … ／ …, which would …"),
        ("追加", "Moreover, … ／ Furthermore, … ／ In addition, …"),
        ("仮定", "If …, … would … ／ Without …, … would …"),
        ("結論", "For these reasons, I believe that … ／ Therefore, …"),
    ]
    v_rows = [
        ("増やす・高める", "increase", "boost ／ enhance ／ raise"),
        ("減らす", "reduce", "cut ／ lower ／ lessen ／ curb"),
        ("和らげる", "make … easier", "ease ／ alleviate ／ relieve"),
        ("引き起こす", "cause", "lead to ／ result in ／ give rise to"),
        ("取り組む", "solve", "address ／ tackle ／ deal with ／ cope with"),
        ("促す", "make people do", "encourage ／ promote ／ motivate"),
        ("問題・欠点", "problem", "issue ／ concern ／ drawback ／ obstacle"),
        ("負担", "heavy work", "burden ／ pressure ／ strain"),
        ("利点", "good point", "benefit ／ advantage"),
        ("重要な", "important", "essential ／ vital ／ crucial"),
        ("お金のかかる", "expensive", "costly"),
        ("人手不足", "not enough workers", "a labor shortage"),
    ]
    s = "".join(f'<tr><td>{a}</td><td class="en">{b}</td></tr>' for a, b in s_rows)
    e = "".join(f'<tr><td>{a}</td><td class="en">{b}</td></tr>' for a, b in e_rows)
    v = "".join(f'<tr><td>{a}</td><td class="en">{b}</td><td class="en">{c}</td></tr>' for a, b, c in v_rows)
    return f"""
<h2 class="sec"><span class="no">5</span>使える表現集</h2>
<div class="cols2">
<div><h3 class="sub">要約で使える</h3><table class="t"><tr><th style="width:30%">働き</th><th>表現</th></tr>{s}</table></div>
<div><h3 class="sub">意見論述で使える</h3><table class="t"><tr><th style="width:22%">働き</th><th>表現</th></tr>{e}</table></div>
</div>
<h3 class="sub">言い換え用の語彙（準1級らしい語）</h3>
<table class="t"><tr><th style="width:18%">意味</th><th style="width:22%">基本の言い方</th><th>言い換え</th></tr>{v}</table>
<p class="small muted">★ 使う前に、解答例の中でどう使われているかを確認してから自分の答案に入れること。意味があいまいなまま使うと、語彙の減点につながります。</p>
"""


def howto():
    steps = [
        ("STEP 1", "<b>時間を計って書く</b>　Set 1 は時間無制限・辞書OK。Set 2・3 は要約20分・意見論述25分、Set 4 からは本番ペース（要約15分・意見論述20分）。"),
        ("STEP 2", "<b>語数を数える</b>　5語ごとに「／」。範囲外ならその場で直す。"),
        ("STEP 3", "<b>セルフチェック</b>　8 のチェックリストで1項目ずつ確認する。"),
        ("STEP 4", "<b>解答例と比べる</b>（③を開く）　要約は「3つの要点が入っているか」と言い換え表、意見論述は構成と具体例の深さを比べる。自分では書けなかった表現に線を引き、<b>表現ストックノート</b>に写す。"),
        ("STEP 5", "<b>何も見ずに書き直す</b>　解答例を写すのではなく、<b>自分の答案を直す</b>。書き直したものが「自分の完成版」。"),
        ("STEP 6", "<b>LINE で送る</b>　書き直した答案を写真で送ってください。添削して返します。直しを清書して表現ストックに追加したら1題クリア。"),
    ]
    st = "".join(f'<div class="step"><div class="s">{a}</div><div>{b}</div></div>' for a, b in steps)
    week = [
        ("1日目", "要約を解く（STEP 1〜4）"),
        ("2日目", "要約を書き直す（STEP 5）→ LINE で送る"),
        ("3日目", "意見論述を解く（STEP 1〜4）"),
        ("4日目", "意見論述を書き直す（STEP 5）→ LINE で送る"),
        ("5日目", "添削を見て清書・表現ストックに追加"),
        ("6〜7日目", "予備日。余裕があれば、意見論述を<b>反対の立場</b>で「立場＋理由2つ」だけメモする"),
    ]
    wk = "".join(f'<tr><td>{a}</td><td>{b}</td></tr>' for a, b in week)
    return f"""
<h2 class="sec"><span class="no">6</span>問題演習の進め方</h2>
<h3 class="sub">1題ごとの6ステップ</h3>
{st}
<h3 class="sub">1週間で1セット（要約1題＋意見論述1題）</h3>
<table class="t plan">{wk}</table>
<div class="box tip"><div class="bh">毎日のルーティン（リスニング対策とセットで）</div>
<b>長文の音読 10分</b>＋<b>英検の音源を聴く</b>（同じ音源のくり返しでOK）。ライティングの解答例や、自分の書き直した答案を音読するのも効果的です。
書いた表現が口から出るようになると、本番で書くスピードも上がります。</div>
"""


def plan():
    rows = [
        ("第1週", "このプリントの 1〜5 を読む。例題（要約・意見論述）を自分でも書いてみる。意見論述の4段落の型を覚える", "時間無制限"),
        ("第2週", "Set 1", "時間無制限・辞書OK"),
        ("第3週", "Set 2", "要約20分・意見論述25分"),
        ("第4週", "Set 3", "要約20分・意見論述25分"),
        ("第5週", "Set 4", "本番ペース（要約15分・意見論述20分）"),
        ("第6週", "Set 5", "本番ペース"),
        ("第7週", "Set 6", "本番ペース"),
        ("第8週", "英検の公式サイトの過去問1回分を、筆記90分で通して解く／Set 1〜3 の意見論述を反対の立場で書く", "本番どおり"),
        ("第9週", "過去問をもう1回分／Set 4〜6 の意見論述を反対の立場で書く", "本番どおり"),
        ("第10週", "試験直前。表現ストックと書き直した答案を見直す。本番の時間で1セット通す。新しい問題は増やさない", "—"),
    ]
    tr = "".join(f'<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>' for a, b, c in rows)
    return f"""
<h2 class="sec"><span class="no">7</span>試験までの10週間プラン</h2>
<table class="t plan"><tr><th style="width:12%">週</th><th>やること</th><th style="width:26%">時間</th></tr>{tr}</table>
<p class="small">★ 12月の試験なら、今週を第1週にするとちょうど10週間前後。試験日に合わせて週を詰めたり伸ばしたりしてかまいません。
★ 反対の立場で書くときは、③ の「反対の立場で書くなら」の骨子を参考にする（同じ TOPIC で2本書けるので、演習量が倍になります）。</p>
"""


def checklist():
    s = ["60〜70語に入っている", "3つの段落の要点が全部入っている", "本文の長いフレーズ（5語以上）をそのまま写していない",
         "具体例・数字・固有名詞を入れていない", "自分の意見（I think など）や本文にない情報を入れていない",
         "However / As a result などで要点どうしの関係を示した", "主語と動詞の一致・時制・冠詞・複数形を確認した"]
    e = ["120〜150語に入っている", "1文目で立場をはっきり書いた", "POINTS から2つ選び、1段落に1つずつ書いた",
         "各理由に「説明」と「具体例・結果」がある", "最初と最後で立場がぶれていない（結論で新しい理由を出していない）",
         "同じ単語・表現を何度も繰り返していない", "短縮形（don't など）や口語（kids など）を使っていない",
         "三単現の s・冠詞・数えられる／数えられない名詞・時制を確認した"]
    li = lambda xs: "".join(f"<li>{x}</li>" for x in xs)
    return f"""
<h2 class="sec"><span class="no">8</span>セルフチェックリスト<small>書き終えたら毎回</small></h2>
<div class="cols2">
<div class="box"><div class="bh">要約（60〜70語）</div><ul class="chk">{li(s)}</ul></div>
<div class="box"><div class="bh">意見論述（120〜150語）</div><ul class="chk">{li(e)}</ul></div>
</div>
<h3 class="sub">4つの観点で自己採点（各0〜4点）</h3>
<table class="t">
<tr><th style="width:12%">観点</th><th>見るところ</th><th style="width:12%">点</th></tr>
<tr><td>内容</td><td>要約：3つの要点がそろっているか ／ 意見論述：立場が明確で、理由に説明と具体例があるか</td><td></td></tr>
<tr><td>構成</td><td>段落の組み立てとつなぎ言葉で、流れが分かりやすいか</td><td></td></tr>
<tr><td>語彙</td><td>課題にふさわしい語を正しく使えているか（要約では言い換えができているか）</td><td></td></tr>
<tr><td>文法</td><td>文の形に変化があり、それを正しく使えているか</td><td></td></tr>
</table>
<p class="small muted">★ 自己採点はあくまで目安。迷ったところは LINE で送ってくれれば一緒に確認します。</p>
"""
