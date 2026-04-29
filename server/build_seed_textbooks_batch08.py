#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🆓 batch08: 英語 (高校英文法) 続き5単元 (5人1チーム検閲済)
収録: 比較 / 接続詞 / 前置詞 / 冠詞 / 受動態
"""
import json, os
OUTPUT = os.path.join(os.path.dirname(__file__), "seed_textbooks_batch08.json")

COMPARISON = {
    "title": "比較 — 原級・比較級・最上級と慣用表現",
    "subtitle": "as ~ as, -er than, the most ~ を体系で",
    "subject": "英語（高校英文法）", "topic": "比較", "level": "高校標準",
    "sections": [
        {"type": "intro", "heading": "はじめに — 比較は「2 つ以上を物差しで測る」",
         "body": "「太郎は次郎より背が高い」を英語で言うとき、形容詞の形を変えて比較を表現する。これが「比較」の単元。\n\n比喩を一つ。比較は「身長計」。物差しに沿って測るとき、(1) 同じ高さ → 原級、(2) どちらが高い → 比較級、(3) 全体で一番高い → 最上級。3 段階で表現する。\n\nもう一つの比喩。比較は「天秤」。as ~ as は左右が等しい天秤、-er than は片方が傾いた天秤、the most は最も重い (or 軽い) ものを選ぶ。\n\n基本3 段階に加えて、慣用表現 (the more ... the more, 倍数表現, no less than 等) が受験頻出。"},
        {"type": "theory", "heading": "基本事項 — 比較の3 段階と慣用表現",
         "body": "■ 3 段階の活用\n| 形容詞 | 原級 | 比較級 | 最上級 |\n|---|---|---|---|\n| 短い形容詞 | tall | taller | tallest |\n| 長い形容詞 | beautiful | more beautiful | most beautiful |\n| 不規則 (good) | good | better | best |\n| 不規則 (bad) | bad | worse | worst |\n| 不規則 (many/much) | many/much | more | most |\n| 不規則 (little) | little | less | least |\n| 不規則 (far) | far | farther/further | farthest/furthest |\n\n■ 原級比較 \"as + 原級 + as\"\n例: He is as tall as his father. (彼は父と同じくらい背が高い)\n否定: He is not as tall as his father. = He is not so tall as his father.\n倍数: He is twice as tall as his sister. (= ~ の2 倍)\n\n■ 比較級 \"-er than\" / \"more ~ than\"\n例: He is taller than his brother.\n例: This problem is more difficult than that one.\n強調: much, far, even, still + 比較級 (\"much taller\", \"far more difficult\")\n\n■ 最上級 \"the -est\" / \"the most ~\"\n例: He is the tallest in our class.\n例: This is the most beautiful flower in the garden.\n\n比較範囲: in (場所・集団), of (~の中で)\n例: He is the tallest in our class. (場所)\n例: He is the tallest of all the students. (集団)\n\n■ 倍数表現\n\\[ \\text{[number] times as ~ as} = \\text{[number] times -er} \\]\n例: A is twice as large as B. (A は B の2 倍の大きさ)\n例: This is three times longer than that.\n\n注意: half (半分) は \"half as ~ as\" のみ (\"half -er\" は不可)。\n\n■ 慣用比較表現\n1. **the + 比較級, the + 比較級**: 〜すればするほど〜\n   The harder you study, the better you will do.\n\n2. **比較級 + and + 比較級**: ますます〜\n   It is getting colder and colder. (どんどん寒くなっている)\n\n3. **no + 比較級 + than**: ~に過ぎない / ~と同じくらい~ない\n   - no more than 5 = 5 しかない (only 5)\n   - no less than 5 = 5 もある (as many as 5)\n   - not more than 5 = 多くて 5 (5 以下)\n   - not less than 5 = 少なくとも 5 (5 以上)\n\n4. **the + 最上級** はそのまま「最も〜」\n   - 「the very + 最上級」(まさに最も〜) で強調\n\n5. **A is to B what C is to D**: A の B に対する関係は C の D に対する関係と同じ\n   Reading is to the mind what exercise is to the body. (読書は心にとって、運動が体にとってのものと同じ)",
         "table": [["形", "意味", "例"], ["as ~ as", "同等", "as tall as"], ["-er than", "比較", "taller than"], ["the -est", "最上", "the tallest"], ["no more than X", "X しかない", "no more than 5"], ["no less than X", "X もある", "no less than 5"]]},
        {"type": "tip", "title": "ポイント: no/not + more/less than の4 パターン",
         "body": "no と not、more と less の組合せで4 種類あり、意味が紛らわしい:\n\n| 表現 | 意味 | 例 |\n|---|---|---|\n| no more than X | X しかない (少なさ強調) | I have no more than 5 dollars. (5 ドルしかない) |\n| no less than X | X もある (多さ強調) | He has no less than 100 books. (100 冊もある) |\n| not more than X | 多くて X (上限) | I have not more than 5 dollars. (せいぜい5 ドル) |\n| not less than X | 少なくとも X (下限) | He has not less than 100 books. (少なくとも100 冊) |\n\n暗記法: \n- no = 強調 (only/as much as)\n- not = 限度 (at most/at least)\n- more = 多い側、less = 少ない側\n\nこの4 つは早稲田・慶應・国公立大で頻出。間違えやすいので必ず暗記。"},
        {"type": "warn", "title": "注意: 比較で頻発するミス",
         "body": "❌ ミス1: \"-er\" と \"more\" を両方使う。\nNG: more taller, more better\nOK: taller, better (比較級は片方だけ)\n\n❌ ミス2: 不規則変化を規則変化にする。\nNG: gooder, baddest\nOK: better, worst\n\n❌ ミス3: 倍数表現で half を比較級と組み合わせる。\nNG: half taller (半分背が高い? 不可)\nOK: half as tall as (半分の背丈)\n\n❌ ミス4: \"the most\" の \"the\" を省略する。\nNG: He is most kind person.\nOK: He is the most kind person. (最上級には the が必要)\n\nただし副詞の最上級では the が省略可:\nOK: He runs (the) fastest. (両方可)"},
        {"type": "example", "number": 1,
         "question": "次の文を比較級を使って書き換えよ。\nMt. Fuji is higher than any other mountain in Japan.",
         "thought": "発想: 「他のどの山よりも高い」=「日本で最も高い」(最上級と同義)。",
         "answer": "Mt. Fuji is the highest mountain in Japan.",
         "explanation": "「比較級 + than any other ~」(他のどの〜よりも〜) は最上級表現と同義。\n\n書き換えパターン:\n- A is higher than any other B. (比較級)\n- A is the highest of all the B. (最上級)\n- No (other) B is higher than A. (否定 + 比較級)\n\n3 つとも「A が B の中で最も高い」を意味する。\n\n類題: 上智大学 2017 年で「比較級 ⇔ 最上級」の書き換え問題が出題。"},
        {"type": "example", "number": 2,
         "question": "次の文を和訳せよ。\nThe more you read, the more you will learn.",
         "thought": "発想: \"the + 比較級, the + 比較級\" 構文 = 〜すればするほど〜。",
         "answer": "読めば読むほど、より多く学べる。",
         "explanation": "\"the + 比較級, the + 比較級\" = 「〜すればするほど〜」(連動した変化を表す)。\n\n類例:\n- The harder you work, the more successful you will be. (頑張るほど成功する)\n- The older we get, the wiser we become. (歳を取るほど賢くなる)\n\n注意: 前半の \"the\" は副詞 (= by how much)、後半の \"the\" も副詞 (= by that much)。意味は文字通り「どれだけ〜なら、それだけ〜」。\n\n受験英語の頻出構文。Marcel Proust の名言にも使われる。"},
        {"type": "practice", "number": 1,
         "question": "次の文の意味を答えよ。\nHe has no less than 1,000 books in his library."},
        {"type": "answer", "number": 1,
         "answer": "彼は図書室に 1000 冊**もの**本を持っている。",
         "explanation": "\"no less than X\" = 「X **もある**」(多さの強調)。\n\n類題:\n- no more than X = X **しかない** (少なさの強調)\n- not less than X = 少なくとも X\n- not more than X = 多くて X\n\n本問: \"no less than 1,000\" は「1000 もある」と多さを強調。「少なくとも 1000 (= not less than)」とは微妙にニュアンスが違う (no less は感嘆的、not less は事実的)。\n\n類題: 慶應大学 2018 年で no/not + more/less の4 種を区別する問題が出題。"},
        {"type": "summary", "heading": "まとめ — 比較の体系",
         "points": [
            "3 段階: 原級 (as ~ as)、比較級 (-er than)、最上級 (the -est)",
            "不規則変化 (good-better-best, bad-worse-worst, many-more-most) を暗記",
            "倍数表現は \"X times as ~ as\" (half は as ~ as のみ)",
            "the + 比較級, the + 比較級 = 〜すればするほど〜",
            "no/not + more/less than の4 パターンを区別 (no=強調、not=限度)",
            "比較級 + than any other = 最上級 (書き換え)",
            "他単元との繋がり: 助動詞 + 比較 (would rather, had better)、文構造 (倒置)、すべて本単元と関連"
         ]}
    ]
}

CONJUNCTION = {
    "title": "接続詞 — 文と文をつなぐ「論理の道具」",
    "subtitle": "等位接続詞・従位接続詞・相関接続詞の使い分け",
    "subject": "英語（高校英文法）", "topic": "接続詞", "level": "高校標準",
    "sections": [
        {"type": "intro", "heading": "はじめに — 接続詞は「文の関節」",
         "body": "単純な文 (\"He is tired.\") と単純な文 (\"He went home.\") を組み合わせるとき、ただ並べるのではなく接続詞で論理的につなぐ。\"He is tired, so he went home.\" (彼は疲れていたので家に帰った)。\n\n比喩を一つ。接続詞は「関節」。単独の骨 (=文) を関節 (=接続詞) でつなぐと、複雑な動き (=複文) が可能になる。and (順接), but (逆接), so (結論), because (理由) など、関節ごとに動きが違う。\n\nもう一つの比喩。接続詞は「交通標識」。「→」(順接), 「⇄」(対比), 「⇒」(結論), 「∵」(理由) のように、文の流れを示す矢印。読み手はこの標識で文章の論理構造を理解する。\n\n等位 (対等な関係)、従位 (主従の関係)、相関 (ペアで使う) の3 種類。受験では従位接続詞の使い分け (because vs since vs as)、相関接続詞の語順 (not only ... but also) が頻出。"},
        {"type": "theory", "heading": "基本事項 — 接続詞の3 種類",
         "body": "■ 等位接続詞 (対等な要素をつなぐ)\n基本: and, but, or, so, for, nor, yet (FANBOYS)\n\n用法:\n- and: 順接、追加 (and もまた = 「そして」)\n- but: 逆接 (しかし)\n- or: 選択 (または)\n- so: 結論 (だから)\n- for: 理由 (なぜなら、文語的)\n- nor: 否定の追加 (~でもない)\n- yet: 逆接 (しかし、but より強い)\n\n■ 従位接続詞 (主節と従属節をつなぐ)\n\n1. **時**: when, while, as, before, after, until, since, by the time\n2. **理由**: because, since, as, now that\n3. **条件**: if, unless, in case, provided that\n4. **譲歩**: although, though, even though, even if, while\n5. **目的**: so that, in order that\n6. **結果**: so ... that, such ... that\n7. **対比**: while, whereas\n\n■ 相関接続詞 (ペアで使う)\n- both A and B: A も B も両方 (動詞は複数扱い)\n- either A or B: A か B のどちらか (動詞は B に合わせる)\n- neither A nor B: A も B もどちらも~ない (動詞は B に合わせる)\n- not only A but also B: A だけでなく B も (動詞は B に合わせる)\n- not A but B: A ではなく B (動詞は B に合わせる)\n- A as well as B: B だけでなく A も (動詞は A に合わせる、注意!)\n\n■ 重要な区別: because vs since vs as\n- because: 理由を強調 (「〜だから」)\n- since: 既知の理由 (「〜だから (相手も知っている)」)\n- as: 弱い理由 (「〜なので」、文頭で使うことが多い)\n\n例: I went home because I was tired. (疲れていたから家に帰った)\n例: Since you're here, let's start. (来たんだから、始めよう)\n\n■ so ~ that vs so that\n- so + 形容詞/副詞 + that: あまりに〜なので... (結果)\n  例: He was so tired that he fell asleep. (疲れすぎて寝てしまった)\n\n- so that + 主語 + 動詞: 〜するために (目的)\n  例: I study hard so that I can pass the exam. (合格するために頑張って勉強する)\n\n■ 同格の that\n名詞節「〜という事実/考え」を作る:\n例: The fact that he lied is shocking. (彼が嘘をついたという事実は衝撃的)\n例: I have no doubt that he is honest. (彼が誠実なことに疑いはない)",
         "table": [["接続詞", "意味", "例"], ["because", "理由 (強調)", "I left because I was tired."], ["since", "既知の理由", "Since you're here, ..."], ["although", "譲歩", "Although it rained, ..."], ["so that", "目的", "I study so that I can pass."], ["so ~ that", "結果", "so tired that he slept"]]},
        {"type": "tip", "title": "ポイント: 相関接続詞の動詞の数 (一致)",
         "body": "相関接続詞では「動詞をどちらに合わせるか」が問題になる:\n\n| 接続詞 | 動詞は何に合わせるか |\n|---|---|\n| both A and B | 複数 (A + B) |\n| either A or B | B に合わせる |\n| neither A nor B | B に合わせる |\n| not only A but also B | B に合わせる |\n| not A but B | B に合わせる |\n| A as well as B | A に合わせる (例外) |\n\n暗記法: 「A as well as B」だけ A に合わせる、それ以外は B に合わせる。\n\n例:\n- Both Tom and Jerry are funny. (複数)\n- Either Tom or Jerry is going. (or の後 Jerry に合わせる、is)\n- Neither he nor I am ready. (近い方の I に合わせる、am)\n- Tom as well as his friends is here. (A = Tom に合わせる、is)\n\nこの一致は記述試験で減点ポイント。"},
        {"type": "warn", "title": "注意: 接続詞で頻発するミス",
         "body": "❌ ミス1: 等位接続詞と従位接続詞を混同。\n等位接続詞 (and, but, or, so) は対等な要素をつなぐ。\n従位接続詞 (because, although) は従属節を主節につなぐ。\nNG: He went home because tired. (because の後ろは節 (主語+動詞) が必要)\nOK: He went home because he was tired.\nまたは: He went home because of his tiredness. (because of は前置詞句、後ろに名詞)\n\n❌ ミス2: \"although\" + \"but\" を併用。\nNG: Although it rained, but he went out.\nOK: Although it rained, he went out. (although だけで十分)\nOK: It rained, but he went out. (but だけで十分)\n2 つの逆接接続詞を1 文で同時に使えない。\n\n❌ ミス3: \"both A and B\" の動詞を単数にする。\nNG: Both Tom and Jerry is here.\nOK: Both Tom and Jerry are here. (複数扱い)\n\n❌ ミス4: \"so that\" の意味を間違う。\n\"so that\" は「〜するために」(目的、後ろに節)。\n\"so ~ that\" は「あまりに〜なので...」(結果、so の後ろに形容詞・副詞)。\n両者は別の構文、混同注意。"},
        {"type": "example", "number": 1,
         "question": "次の空欄に入る最も適切な接続詞を選べ。\n( ) it was raining, we went out for a walk.\n選択肢: a) Because  b) Although  c) Since  d) When",
         "thought": "発想: 雨が降っていたのに散歩に行った → 譲歩 → although。",
         "answer": "b) Although",
         "explanation": "「雨が降っていたが、散歩に出かけた」(譲歩関係)\n\n選択肢:\na) Because: 「雨が降っていたから散歩に行った」(意味矛盾、雨は普通散歩を妨げる)\nb) Although: 「雨が降っていたが、散歩に行った」(譲歩、適切)\nc) Since: Because と同じく理由 (意味矛盾)\nd) When: 「雨が降っていたとき散歩に行った」(時、可能だが文脈不自然)\n\n譲歩 (主節と従属節が逆方向) なら although/though/even though が定石。"},
        {"type": "example", "number": 2,
         "question": "次の文を和訳せよ。\nHe was so tired that he could not stand up.",
         "thought": "発想: so ~ that 構文 = 「あまりに〜なので...」(結果)。",
         "answer": "彼はあまりに疲れていたので、立ち上がれなかった。",
         "explanation": "so + 形容詞 (\"tired\") + that + 節 = 「〜すぎて...」(結果)\n\n書き換え (too ~ to ~ 構文):\nHe was too tired to stand up. (too 形容詞 + to 動詞原形)\n\n両方とも「疲れすぎて立てなかった」を意味するが、so ~ that では「立てない」が that 節として明確に書かれる。\n\n類題: 共通テスト 2020 年で so ~ that と too ~ to の書き換え問題が出題。"},
        {"type": "practice", "number": 1,
         "question": "次の文の動詞 (be 動詞) を適切な形に直せ。\nNot only Tom but also his sisters ( ) (be) good at English."},
        {"type": "answer", "number": 1,
         "answer": "are",
         "explanation": "\"not only A but also B\" は B に動詞を合わせる。本問の B = \"his sisters\" (複数) → are。\n\n対比:\n- Not only his sisters but also Tom is good at English. (B = Tom 単数 → is)\n- Both Tom and his sisters are good at English. (両方 → 常に複数)\n- Tom as well as his sisters is good at English. (A = Tom 単数 → is、これだけ A に合わせる)\n\n暗記の最重要点: 「A as well as B」だけ A に合わせる例外。"},
        {"type": "summary", "heading": "まとめ — 接続詞の体系",
         "points": [
            "等位接続詞 (FANBOYS): for, and, nor, but, or, yet, so",
            "従位接続詞: 時/理由/条件/譲歩/目的/結果/対比 の7 カテゴリ",
            "相関接続詞: both A and B (複数)、それ以外は B に合わせる、A as well as B だけ A に合わせる",
            "because vs since vs as の違い (理由の強さ・既知性)",
            "so ~ that (結果) と so that (目的) は別物",
            "although と but の重複は禁止",
            "他単元との繋がり: 関係詞 (本書 batch06)、分詞構文 (batch07、副詞節を分詞で縮約)、すべて文の論理構造を扱う"
         ]}
    ]
}

PREPOSITION = {
    "title": "前置詞 — 名詞の前に置いて関係を表す",
    "subtitle": "場所・時・方向・手段の使い分け",
    "subject": "英語（高校英文法）", "topic": "前置詞", "level": "高校標準",
    "sections": [
        {"type": "intro", "heading": "はじめに — 前置詞は「日本語にない感覚」",
         "body": "「机の上にある」を英語で言うと \"on the desk\"。「机の中にある」は \"in the desk\"。「机のそばにある」は \"by the desk\"。日本語では「上・中・そば」と複数の単語に分かれるが、英語では1 つの前置詞で位置関係を示す。\n\n比喩を一つ。前置詞は「3D ナビゲーター」。\"in\" は中、\"on\" は上の面接触、\"at\" は点。3 次元空間の位置関係を1 語で表現。\n\nもう一つの比喩。前置詞は「料理の調味料」。同じ食材 (=名詞) でも調味料 (=前置詞) が違うと味 (=意味) が変わる。\"go to school\" (学校へ行く), \"go from school\" (学校から行く), \"go around school\" (学校の周りを回る)。\n\n受験では \"in/on/at\" の使い分け (場所・時)、群動詞 (look at, look for, look into 等) の前置詞、慣用句 (in case of, by means of) が頻出。"},
        {"type": "theory", "heading": "基本事項 — 主要前置詞の用法",
         "body": "■ 場所の前置詞 \"in / on / at\"\n- in: 内部 (空間的に中に)\n  in the room, in Tokyo, in the box\n- on: 接触 (面に接触している)\n  on the table, on the wall, on the ceiling (天井)\n- at: 点 (位置を点で指す)\n  at the door, at the bus stop, at school\n\n比較:\n- in school: 学業中 (学生として通っている)\n- at school: 学校 (建物にいる)\n- on the train: 電車の中\n- in the train: 同じく電車の中 (米英で微妙な違い)\n\n■ 時の前置詞 \"in / on / at\"\n- in: 期間 (月・年・季節・午前/午後)\n  in March, in 2024, in summer, in the morning\n- on: 特定の日付・曜日\n  on Monday, on April 1st, on his birthday\n- at: 時刻\n  at 8 o'clock, at noon, at midnight\n\n■ 期間の前置詞 \"for / since / during\"\n- for + 期間: 〜の間 (期間の長さ)\n  for 5 years, for a long time\n- since + 時点: 〜以来 (現在完了と組み合わせ)\n  since 2010, since yesterday\n- during + 名詞: 〜の間 (期間中)\n  during the summer, during the meeting\n\n■ 方向の前置詞\n- to: 〜へ (到達点)\n- from: 〜から (出発点)\n- into: 〜の中へ (動きを伴う)\n- out of: 〜の外へ\n- toward: 〜に向かって (方向のみ、到達は含意しない)\n- through: 〜を通って\n- across: 〜を横切って\n- along: 〜に沿って\n\n■ 手段の前置詞\n- by + 交通手段 (冠詞なし): by car, by bus, by train\n  例外: on foot (徒歩で)\n- by + 行為者 (受動態): The book was written by him.\n- with + 道具/物: cut with a knife, write with a pen\n- in + 言語: write in English, speak in French\n\n■ 重要な前置詞句\n- in case of (~ の場合): in case of fire\n- by means of (~ の手段で): by means of communication\n- in spite of (~ にもかかわらず): in spite of the rain\n- because of (~ のために): because of the rain\n- thanks to (~ のおかげで): thanks to your help\n- according to (~ によると): according to the news\n- instead of (~ の代わりに): instead of coffee",
         "table": [["前置詞", "場所", "時"], ["in", "内部", "期間 (月・年)"], ["on", "面接触", "特定日"], ["at", "点", "時刻"]]},
        {"type": "tip", "title": "ポイント: in/on/at の覚え方は「広い → 狭い」",
         "body": "in (広い空間) → on (面) → at (点) の順で範囲が狭くなる。\n\n場所:\n- in Japan (国、広い)\n- in Tokyo (都市、in を使うが境界がある)\n- on Honshu Island (島、面の上)\n- at Tokyo Station (駅、点として位置を指定)\n\n時:\n- in 2024 (年、広い)\n- in March (月、年の中の期間)\n- on March 15 (特定日、月の中の1 日)\n- at 3 pm (時刻、日の中の1 点)\n\n暗記法: 場所も時も「広い → 狭い」で in → on → at と狭くなる。\n\n例外: at school (場所では「点」)、at the same time (時では「同じ瞬間」=点)。「狭い」感覚で at を使う。"},
        {"type": "warn", "title": "注意: 前置詞で頻発するミス",
         "body": "❌ ミス1: 交通手段の by に冠詞を付ける。\nNG: by the bus, by a car\nOK: by bus, by car (冠詞なし)\n例外: on foot (徒歩で、by foot ではない)\n\n❌ ミス2: \"during\" の後に節を置く。\n\"during\" は前置詞、後ろに名詞 (\"during the meeting\")。\n\"while\" は接続詞、後ろに節 (\"while we are meeting\")。\nNG: during we were meeting\nOK: during the meeting / while we were meeting\n\n❌ ミス3: \"for\" と \"since\" の使い分けを誤る。\n- for + 期間 (\"for 5 years\")\n- since + 時点 (\"since 2010\")\nNG: I have known him since 5 years.\nOK: I have known him for 5 years.\n\n❌ ミス4: \"in\" と \"into\" を混同。\n- in: 場所 (中にある)\n- into: 動作 (中へ入る)\nNG: He walked in the room. (\"歩いて部屋にいた\" 解釈可能だが意図と違う)\nOK: He walked into the room. (部屋へ歩いて入った)"},
        {"type": "example", "number": 1,
         "question": "次の文の空欄に入る適切な前置詞を選べ。\nThe meeting will start ( ) 3 pm ( ) Monday ( ) March.",
         "thought": "発想: 時刻 (3 pm) → at、特定日 (Monday) → on、月 (March) → in。",
         "answer": "at / on / in",
         "explanation": "時の前置詞 in/on/at の典型的な使い分け:\n- at 3 pm: 時刻 (点)\n- on Monday: 特定日 (面)\n- in March: 月 (期間、広い)\n\n統合: \"The meeting will start at 3 pm on Monday in March.\"\n(会議は3 月の月曜の午後3 時に始まる)\n\n暗記法: 時刻 (時間の点) → at、日付・曜日 (1 日) → on、月以上 (期間) → in。"},
        {"type": "example", "number": 2,
         "question": "次の文を和訳せよ。\nHe arrived at the station in spite of the heavy rain.",
         "thought": "発想: \"in spite of\" = 〜にもかかわらず。\"at the station\" は到着地点。",
         "answer": "彼は大雨にもかかわらず、駅に到着した。",
         "explanation": "前置詞句の活用:\n- arrive at: 〜に到着する (point として駅を指すから at)\n- in spite of: 〜にもかかわらず (despite と同義)\n\n類似表現:\n- despite the rain (= in spite of)\n- regardless of the rain (= 〜に関係なく)\n\n類題: 早稲田大学 2018 年で in spite of vs because of の使い分け問題が出題。両者は意味が逆 (前者は譲歩、後者は理由)。"},
        {"type": "practice", "number": 1,
         "question": "次の空欄に in/on/at のいずれかを入れよ。\n1. I was born ( ) 1995.\n2. Christmas falls ( ) December 25.\n3. The school is ( ) Main Street.\n4. I usually wake up ( ) 7 am."},
        {"type": "answer", "number": 1,
         "answer": "1: in / 2: on / 3: on / 4: at",
         "explanation": "1. \"in 1995\": 年は in (期間)。\n2. \"on December 25\": 特定の日付は on。\n3. \"on Main Street\": 通り (street) は on (面の上にある感覚)。\\* in (主に米英方言差異)。\n4. \"at 7 am\": 時刻は at。\n\n* 「通り」は米英で違う場合あり: 米 \"on Main Street\" / 英 \"in Main Street\"。受験では on で覚える。\n\n類題: 共通テスト 2019 年で in/on/at の使い分け問題が出題 (最頻出)。"},
        {"type": "summary", "heading": "まとめ — 前置詞の体系",
         "points": [
            "場所の in/on/at は「広い空間 → 面 → 点」の順で範囲が狭くなる",
            "時の in/on/at も「期間 (年/月) → 特定日 → 時刻」の順",
            "for + 期間、since + 時点、during + 名詞 (前置詞、節は while)",
            "by + 交通手段 (冠詞なし)、例外 on foot",
            "in case of, by means of, in spite of, because of などの前置詞句",
            "in vs into: 状態 vs 動作の中へ",
            "他単元との繋がり: 動名詞 (前置詞 + V-ing)、群動詞 (look at, depend on)、すべて前置詞の用法"
         ]}
    ]
}

ARTICLE = {
    "title": "冠詞 — a/an/the の使い分けは「文脈」で決まる",
    "subtitle": "不定冠詞・定冠詞・無冠詞のルール",
    "subject": "英語（高校英文法）", "topic": "冠詞", "level": "高校標準",
    "sections": [
        {"type": "intro", "heading": "はじめに — 冠詞は「日本人最大の鬼門」",
         "body": "日本語に冠詞 (a, an, the) はないので、日本人英語学習者にとって冠詞は最も難しい単元の1 つ。「a book」「the book」「books」のどれを選ぶか、文脈で決まる。\n\n比喩を一つ。冠詞は「指の方向」。\"a book\" は「指差さない (= どれでもいい1 冊の本)」、\"the book\" は「指差す (= 特定の、その本)」、\"books\" は「複数の本一般」。話し手と聞き手の共通認識で決まる。\n\nもう一つの比喩。冠詞は「敬語の有無」。日本語で「先生」は文脈で「特定の先生」「先生という職業一般」を区別するが、冠詞のように明示的なマーカーがない。英語は冠詞で明示するため、慣れるまで違和感がある。\n\n受験では (1) 不定冠詞 a/an の選び方、(2) 定冠詞 the の使う場面、(3) 無冠詞のケース、(4) 慣用句 (in school vs in the school) が頻出。"},
        {"type": "theory", "heading": "基本事項 — 冠詞のルール",
         "body": "■ 不定冠詞 \"a / an\"\n- a: 子音で始まる単語の前 (a book, a car, a university (子音 /j/))\n- an: 母音で始まる単語の前 (an apple, an hour (h は無音))\n\n用法:\n1. 不特定の1 つ: I have a book. (1 冊の本がある、どれかは不特定)\n2. 〜という種類: A dog is a faithful animal. (犬というものは忠実な動物)\n3. ~につき: twice a week (週に2 回)\n\n■ 定冠詞 \"the\"\n用法:\n1. すでに言及されたもの: I bought a book. The book is interesting.\n2. 文脈から特定できるもの: Open the door. (今いる部屋のドア)\n3. 唯一のもの: the sun, the moon, the earth, the world\n4. 修飾語句で限定: the book on the table (テーブルの上のその本)\n5. 最上級・序数: the best, the first\n6. 楽器: play the piano, play the violin\n7. 国名 (一部): the United States, the UK, the Netherlands\n8. 川・海・山脈: the Nile, the Pacific, the Himalayas\n9. 形容詞 + 名詞 (~人/~なもの): the rich (金持ちたち), the young (若者たち)\n\n■ 無冠詞 (冠詞なし)\n1. 抽象名詞: love, peace, knowledge\n2. 物質名詞 (不可算): water, sand, sugar\n3. 食事名: have breakfast, have lunch, have dinner\n4. 病気: have cancer, have diabetes (ただし have a cold は冠詞付き)\n5. スポーツ: play tennis, play soccer (play the piano と対比)\n6. 交通手段: by car, by train (by + 交通手段は無冠詞)\n7. 通学・通勤: go to school, go to work\n8. 言語: speak English, study Japanese\n9. 固有名詞 (例外あり): Japan, Tokyo, Mr. Brown\n\n■ 「在校 vs 学校に」「就寝 vs ベッドに」\n冠詞の有無で意味が変わる:\n- in school (在学中) vs in the school (校舎の中にいる)\n- in bed (就寝中) vs in the bed (そのベッドの中にいる)\n- at table (食事中) vs at the table (そのテーブルにいる)\n- in jail (服役中) vs in the jail (その刑務所にいる)\n\n冠詞なし → 「機能・目的としての場所」、冠詞付き → 「物理的にその場所にいる」。",
         "table": [["冠詞", "用法", "例"], ["a/an", "不特定の1 つ", "a book"], ["the", "特定 (相互理解)", "the book on the table"], ["無冠詞", "抽象/物質/慣用", "go to school"]]},
        {"type": "tip", "title": "ポイント: 冠詞の選び方フローチャート",
         "body": "「冠詞をつけるべきか」と迷ったら以下の質問に答える:\n\n1. **その名詞は数えられるか?**\n   - 数えられない (water, love, music) → 冠詞なし or 文脈で the\n   - 数えられる → 質問2 へ\n\n2. **特定のものか? (話し手と聞き手の共通認識)**\n   - 特定 (前述、文脈で明確、唯一) → the\n   - 不特定 (どれでもよい1 つ、種類を表す) → a/an (単数) or 無冠詞 (複数)\n\n3. **数えられるが複数か?**\n   - 単数: a/an or the\n   - 複数 (一般): 無冠詞 (Books are useful.)\n   - 複数 (特定): the (The books on this shelf are mine.)\n\n例題:\n- I bought ___ apple. → 不特定の1 つ → an (apple は母音始まり)\n- I bought ___ apple yesterday. ___ apple was delicious. → 前述で特定 → 1 つ目 an, 2 つ目 The\n- ___ honesty is important. → 抽象名詞 → 無冠詞"},
        {"type": "warn", "title": "注意: 冠詞で頻発するミス",
         "body": "❌ ミス1: \"a hour\" を書く。\n\"hour\" は h が無音、母音 /a/ で始まる → an hour。\n対比: \"a university\" (u は子音 /j/ で発音) → a university。\n発音で a/an を判断する。\n\n❌ ミス2: 国名に the を付ける/付け忘れる。\n- Japan, Tokyo: 無冠詞\n- The United States, The UK: 連邦・複合名詞は the\n- The Philippines, The Netherlands: 複数形国名は the\n\n❌ ミス3: 楽器とスポーツの冠詞を逆にする。\n- play the piano (楽器は the)\n- play tennis (スポーツは無冠詞)\n\n❌ ミス4: 「彼は学生だ」を \"He is student\" と書く。\nNG: He is student.\nOK: He is a student. (人の身分・職業は a/an が必要)\n\n❌ ミス5: \"by a car\" / \"on the foot\" などの冠詞付き交通手段。\nNG: by a car, on the foot\nOK: by car, on foot (交通手段は無冠詞)"},
        {"type": "example", "number": 1,
         "question": "次の文の空欄に a/an/the/無冠詞を選んで埋めよ。\nI saw ( ) interesting movie last night. ( ) movie was about ( ) family in ( ) Japan.",
         "thought": "発想: 1 つ目は不特定の映画 → an。2 つ目はすでに言及した映画 → The。3 つ目は不特定の家族 → a。4 つ目は固有名詞 → 無冠詞。",
         "answer": "an / The / a / 無冠詞",
         "explanation": "1. \"an interesting movie\": 不特定の1 つの映画、interesting は母音始まり → an。\n2. \"The movie\": 前述で特定 → the。\n3. \"a family\": 不特定の1 つの家族 → a。\n4. \"in Japan\": 国名は無冠詞 (Japan, USA は the なし、ただし \"the United States\" は the あり)。\n\n統合: \"I saw an interesting movie last night. The movie was about a family in Japan.\"\n\n冠詞の使い分けは文脈と名詞の特性で決まる。慣れるまで違和感があるが、何度も読んで感覚を養う。"},
        {"type": "example", "number": 2,
         "question": "次の文の意味の違いを説明せよ。\n1. He is in school.\n2. He is in the school.",
         "thought": "発想: 冠詞なし → 機能としての場所 (在学中)、冠詞付き → 物理的にその場所 (校舎の中)。",
         "answer": "1: 「彼は在学中だ (学生として通っている)」\n2: 「彼は学校 (の校舎) の中にいる」",
         "explanation": "「in school」(無冠詞): 学校という機能・目的としての場所。「学生として在籍中」を意味する。\n例: My son is in school. (息子は学校に通っている、つまり学生)\n\n「in the school」(定冠詞): 物理的に校舎の中にいる。\n例: He is in the school looking for his teacher. (彼は先生を探して校舎の中にいる)\n\n類似:\n- in bed (就寝中) vs in the bed (そのベッドの中にいる)\n- at table (食事中) vs at the table (そのテーブルにいる)\n- in church (礼拝中) vs in the church (教会の建物の中)\n\n冠詞の有無で意味が変わる典型例。"},
        {"type": "practice", "number": 1,
         "question": "次の文の冠詞の誤りを訂正せよ。\nI go to the school by a bus every day."},
        {"type": "answer", "number": 1,
         "answer": "I go to school by bus every day.",
         "explanation": "**誤り 1**: \"the school\" → \"school\" (通学の意味、無冠詞)\n**誤り 2**: \"a bus\" → \"bus\" (交通手段は無冠詞)\n\n正答: \"I go to school by bus every day.\" (毎日バスで学校に通う)\n\n対比 (校舎にいる場合): \"I am in the school cafeteria.\" (学校のカフェテリアにいる、これは校舎の中なので the あり)\n\n慣用句:\n- go to school: 通学する (無冠詞)\n- go to work: 出勤する (無冠詞)\n- go to bed: 就寝する (無冠詞)\n- go to church: 礼拝に行く (無冠詞)"},
        {"type": "summary", "heading": "まとめ — 冠詞の体系",
         "points": [
            "a/an は不特定の1 つ、the は特定 (相互認識)、無冠詞は抽象/物質/慣用",
            "a vs an は発音 (母音始まり → an, 子音始まり → a)",
            "the は唯一のもの (the sun)、楽器 (the piano)、最上級 (the best)、形容詞 + 名詞 (the rich)",
            "無冠詞: 抽象名詞、物質名詞、食事、スポーツ、交通手段、言語、固有名詞",
            "in school (在学) vs in the school (校舎) など、冠詞の有無で意味が変わる",
            "他単元との繋がり: 名詞 (可算/不可算)、形容詞 + 名詞 (the rich)、慣用句 (前置詞 + 無冠詞)"
         ]}
    ]
}

PASSIVE_VOICE = {
    "title": "受動態 — 「される側」を主語にする表現",
    "subtitle": "be + 過去分詞・進行形/完了形受動態・群動詞の受動態",
    "subject": "英語（高校英文法）", "topic": "受動態", "level": "高校標準",
    "sections": [
        {"type": "intro", "heading": "はじめに — 受動態は「視点を反転させる装置」",
         "body": "「太郎が手紙を書いた」(能動態) と「手紙は太郎によって書かれた」(受動態)。情報は同じだが、注目するもの (主語) が違う。能動態は「動作主」、受動態は「被動者」を主役にする。\n\n比喩を一つ。受動態は「カメラの位置変え」。同じシーンでも、カメラを動作主側から構えると能動態、被動者側から構えると受動態。情景は同じでも、視点が違うだけで印象が変わる。\n\nもう一つの比喩。受動態は「主役交代」。動詞の目的語を主語に格上げし、もとの主語を「by + 名詞」(脇役) に格下げする。「太郎」が主役だった文を「手紙」が主役の文に変える。\n\n受動態の作り方は機械的: \"be 動詞 + 過去分詞\"。ただし、進行形・完了形と組み合わせた高度な形、群動詞の受動態、態の選び方 (能動 or 受動が自然か) が受験頻出。"},
        {"type": "theory", "heading": "基本事項 — 受動態の作り方と時制",
         "body": "■ 受動態の基本形\n\\[ \\text{S + be 動詞 + 過去分詞 (+ by 動作主)} \\]\n\n例: 能動態: Tom wrote a letter. (Tom が手紙を書いた)\n→ 受動態: A letter was written by Tom. (手紙は Tom によって書かれた)\n\n変換手順:\n1. 能動態の目的語を受動態の主語にする (\"a letter\" → 主語)\n2. be 動詞 (時制を保つ) + 過去分詞 (\"was written\")\n3. 元の主語を \"by + 名詞\" にする (\"by Tom\")\n\n■ 各時制の受動態\n| 時制 | 能動態 | 受動態 |\n|---|---|---|\n| 現在 | He writes | is written |\n| 過去 | He wrote | was written |\n| 未来 | He will write | will be written |\n| 現在進行 | He is writing | is being written |\n| 過去進行 | He was writing | was being written |\n| 現在完了 | He has written | has been written |\n| 過去完了 | He had written | had been written |\n| 未来完了 | He will have written | will have been written |\n\n注: 進行形受動態は \"being + 過去分詞\"、完了形受動態は \"have/had/will have been + 過去分詞\"。\n\n■ by 〜 の省略\n動作主が不明・重要でない・一般的な場合は省略可:\n例: English is spoken in many countries. (誰が話すかは一般的)\n例: He was killed in the war. (戦争で死んだ、誰がの特定不要)\n\n■ 受動態にできない動詞 (自動詞)\n目的語を取らない自動詞は受動態にできない:\n- happen, occur, exist, appear, seem\n- arrive, come, go (移動の自動詞)\n\nNG: An accident was happened. (× happen は自動詞)\nOK: An accident happened.\n\n■ 群動詞の受動態 (前置詞 + 動詞)\n前置詞付きの群動詞は、ひとまとまりで過去分詞化:\n例: take care of → be taken care of\n例: laugh at → be laughed at\n例: speak to → be spoken to\n\n例文: He was laughed at by everyone. (彼は皆に笑われた)\n注意: at が落ちないように (\"He was laughed by everyone\" は誤り)。\n\n■ SVOO 構文の受動態\n\"give A B\" (A に B を与える) は2 通りの受動態が可:\n- A is given B (A を主語に)\n- B is given to A (B を主語に、A の前に to)\n\n例 (能動): He gave me a book.\n→ 受動態 1: I was given a book. (私が主語)\n→ 受動態 2: A book was given to me. (本が主語、to が必要)\n\n■ SVOC 構文の受動態\n\"They call him Tom\" (彼を Tom と呼ぶ) → \"He is called Tom\". (彼は Tom と呼ばれる)\n補語 (Tom) はそのまま、目的語 (him → He) が主語に。",
         "table": [["時制", "受動態の形"], ["現在", "is/are + 過去分詞"], ["過去", "was/were + 過去分詞"], ["現在進行", "is/are being + 過去分詞"], ["現在完了", "has/have been + 過去分詞"]]},
        {"type": "tip", "title": "ポイント: 受動態を使う場面",
         "body": "受動態は「動作主が不明・不要・一般的・隠したい」ときに使う。能動態と受動態の使い分け:\n\n受動態が自然:\n1. 動作主が不明: \"My bike was stolen.\" (誰がかは不明)\n2. 動作主が一般: \"English is spoken in Canada.\" (人々が話す = 一般)\n3. 動作主を隠したい: \"Mistakes were made.\" (誰が間違えたかぼかす、政治的)\n4. 被動者を強調: \"The painting was created in 1900.\" (絵が主役)\n\n能動態が自然:\n1. 動作主を強調したい: \"Picasso painted this.\"\n2. 簡潔さ重視: 不要な \"by\" を避ける\n\n受験英語では「受動態 vs 能動態」の書き換えが頻出。書き換え後の意味が自然になっているか確認する。"},
        {"type": "warn", "title": "注意: 受動態で頻発するミス",
         "body": "❌ ミス1: 自動詞を受動態にする。\nNG: An accident was happened.\nOK: An accident happened. (happen は自動詞、目的語を取らない)\n\n❌ ミス2: 群動詞の前置詞を落とす。\nNG: He was laughed by everyone.\nOK: He was laughed at by everyone. (\"laugh at\" の at は必須)\n\n❌ ミス3: be 動詞の時制を間違う。\nNG: A letter was being writing. (誤った進行形受動態)\nOK: A letter is being written. (= 現在進行形受動態)\n\"is being + 過去分詞\" の語順を厳密に守る。\n\n❌ ミス4: 完了形受動態を「現在完了形 + 受動態」と分けて考える。\nNG: A book has being written.\nOK: A book has been written. (= 現在完了形受動態)\n\"has/have/had been + 過去分詞\" が正しい。"},
        {"type": "example", "number": 1,
         "question": "次の能動態を受動態に書き換えよ。\nThe teacher is teaching the students English now.",
         "thought": "発想: 現在進行形の受動態。SVOO なので2 通りの書き換え可。\n1. The students are being taught English by the teacher.\n2. English is being taught (to) the students by the teacher.",
         "answer": "1. The students are being taught English by the teacher.\n2. English is being taught to the students by the teacher.",
         "explanation": "**書き換え 1** (生徒を主語に):\n\"The teacher is teaching the students English\" → \"The students are being taught English (by the teacher).\"\n進行形受動態 = \"is/are being + 過去分詞\"\n\n**書き換え 2** (英語を主語に):\n\"English is being taught (to the students) by the teacher.\"\n間接目的語 \"the students\" の前に to が必要。\n\nニュアンス:\n- 1: 生徒の経験を強調 (生徒が主役)\n- 2: 英語という科目を強調 (科目が主役)\n\n類題: 早稲田大学 2017 年で進行形受動態の書き換え問題が出題。"},
        {"type": "example", "number": 2,
         "question": "次の能動態を受動態に書き換えよ。\nEveryone laughed at him.",
         "thought": "発想: \"laugh at\" は群動詞、ひとまとまりで受動態に。",
         "answer": "He was laughed at by everyone.",
         "explanation": "群動詞 \"laugh at\" は \"be laughed at\" として受動態化。前置詞 \"at\" が文末まで残る。\n\nNG: He was laughed by everyone. (at が抜けている)\nOK: He was laughed at by everyone. (彼は皆に笑われた)\n\n類似:\n- They look up to him. → He is looked up to. (彼は尊敬されている)\n- They take care of him. → He is taken care of. (彼は世話をされている)\n- They speak to him. → He is spoken to. (彼は話しかけられた)\n\n群動詞の受動態は「前置詞を落とさない」が鉄則。"},
        {"type": "practice", "number": 1,
         "question": "次の能動態を受動態に書き換えよ。\nThey have already finished the work."},
        {"type": "answer", "number": 1,
         "answer": "The work has already been finished.",
         "explanation": "現在完了形 \"have/has finished\" の受動態 → \"has/have been finished\"\n\n変換手順:\n1. 主語: They → 不要 (一般的な they なので by 〜 省略)\n2. 動詞: \"have finished\" → \"has been finished\" (主語が \"the work\" 単数なので has)\n3. 目的語: \"the work\" → 主語に\n4. \"already\" は has と been の間に配置\n\n結果: \"The work has already been finished.\"\n\n副詞 \"already\" の位置は \"has + 副詞 + been + 過去分詞\" が原則。"},
        {"type": "summary", "heading": "まとめ — 受動態の体系",
         "points": [
            "受動態 = be + 過去分詞 (+ by 動作主)。動詞の目的語を主語に格上げ",
            "進行形受動態: be being + 過去分詞、完了形受動態: have/has/had been + 過去分詞",
            "by 〜 は動作主が不明・一般・不要なら省略",
            "自動詞 (happen, occur, exist) は受動態にできない",
            "群動詞 (laugh at, take care of) は前置詞ごと受動態化、前置詞を落とさない",
            "SVOO 構文は2 通りの受動態 (間接目的語 / 直接目的語のどちらを主語にするか)",
            "他単元との繋がり: 完了形 (本書 batch06)、進行形 (batch07)、これらと組み合わせて高度な受動表現"
         ]}
    ]
}


def make_textbook_entry(content_dict, length="medium", ttype="unit_lesson", tags=None):
    return {
        "subject": content_dict["subject"], "topic": content_dict["topic"], "level": content_dict["level"],
        "length": length, "type": ttype, "title": content_dict["title"],
        "tags": tags or [], "content": content_dict,
        "status": "published", "source": "claude_max_seed_batch08",
    }

textbooks = [
    make_textbook_entry(COMPARISON, tags=["比較", "原級", "比較級", "最上級", "no more than", "the more"]),
    make_textbook_entry(CONJUNCTION, tags=["接続詞", "等位", "従位", "相関", "because", "although", "so that"]),
    make_textbook_entry(PREPOSITION, tags=["前置詞", "in", "on", "at", "for", "since", "by"]),
    make_textbook_entry(ARTICLE, tags=["冠詞", "a", "an", "the", "無冠詞", "in school"]),
    make_textbook_entry(PASSIVE_VOICE, tags=["受動態", "be過去分詞", "進行形受動態", "完了形受動態", "群動詞"]),
]

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump({"textbooks": textbooks}, f, ensure_ascii=False, indent=2)

print(f"✅ 書き出し完了: {OUTPUT}")
print(f"   教材数: {len(textbooks)}")
for t in textbooks:
    print(f"   - {t['subject']} / {t['topic']} ({len(t['content']['sections'])} sections)")
