# -*- coding: utf-8 -*-
"""vol.02 「東大・京大の英文はこう読む」— It is A that (強調構文) の識別。

★vol.01 と違い、例文は**実在の入試問題ではない**。
  自塾の教材 scripts/eng_therules/rulehunt03/content.py の原創長文
  「Why Curiosity Outlasts Talent」訓練1 第10文をそのまま使っている。
  判定法「It…that を外して戻る」も同ファイルの正典
  (RULEMAP ⑧ / INSTANCES s=10 の note) に一致させてある。
  だから出典の捏造が無く、unverified は空でよい。
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from build_vol import B, rough_ellipse  # noqa: E402
import theme_vol as T  # noqa: E402


# ── p4 の図: It is と that を「外す」ところを見せる ─────────────────
# ★SVG に日本語を入れない (和文フォントの無い環境で豆腐になる)。
#   x と幅を固定し textLength で強制する (環境ごとの字幅差で注釈がずれないように)。
_L1 = [
    ("it",         186,  26, "#ffffff"),
    ("is",         228,  26, "#ffffff"),
    ("curiosity,", 270, 150, "#ffffff"),
    ("not",        436,  46, T.MUTED),
    ("talent,",    498, 104, "#ffffff"),
    ("that",       618,  64, "#ffffff"),
    ("decides",    698, 116, "#ffffff"),
]
_L2 = [
    ("how",    292, 50, "#ffffff"),
    ("far",    358, 46, "#ffffff"),
    ("a",      420, 18, "#ffffff"),
    ("mind",   454, 68, "#ffffff"),
    ("will",   538, 58, "#ffffff"),
    ("travel", 612, 96, "#ffffff"),
]


def _words(rows, y):
    return "".join(
        f'<text x="{x}" y="{y}" textLength="{w}" lengthAdjust="spacingAndGlyphs" '
        f'font-size="34" fill="{c}" font-family="Georgia,&quot;Liberation Serif&quot;,'
        f'&quot;DejaVu Serif&quot;,serif">{t}</text>'
        for t, x, w, c in rows)


def _diagram():
    ring_it = rough_ellipse(220, 88, 48, 30, rot=-4)
    ring_th = rough_ellipse(650, 88, 44, 28, rot=3, phase=1.1)
    return (
        '<svg width="950" viewBox="0 0 1000 250" fill="none" '
        'xmlns="http://www.w3.org/2000/svg">'
        '<defs>'
        f'<marker id="v2-ar" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" '
        f'markerHeight="6" orient="auto-start-reverse">'
        f'<path d="M2 1L8 5L2 9" fill="none" stroke="{T.PINK}" stroke-width="1.8" '
        f'stroke-linecap="round"/></marker>'
        '</defs>'
        + _words(_L1, 100) + _words(_L2, 168) +
        # 強調される部分 (焦点) に琥珀の下線
        f'<path d="M 270 120 L 602 120" stroke="{T.AMBER}" stroke-width="4" '
        f'stroke-linecap="round"/>'
        # 外す 2 か所: 丸で囲んで、線で消す
        f'<path d="{ring_it}" stroke="{T.PINK}" stroke-width="5" stroke-linecap="round"/>'
        f'<path d="{ring_th}" stroke="{T.PINK}" stroke-width="5" stroke-linecap="round"/>'
        f'<path d="M 176 90 L 264 86" stroke="{T.PINK}" stroke-width="4" '
        f'stroke-linecap="round"/>'
        f'<path d="M 608 90 L 692 86" stroke="{T.PINK}" stroke-width="4" '
        f'stroke-linecap="round"/>'
        # 残りが 1 文になることを示す下向き矢印
        f'<path d="M 500 196 L 500 240" stroke="{T.PINK}" stroke-width="3" '
        f'marker-end="url(#v2-ar)"/>'
        '</svg>')


VOL = dict(
    key="vol02",
    series="東大・京大の英文はこう読む",
    label="vol.02",
    brand="TRILLION ENGLISH ACADEMY",
    handle="@trillion_ai",
    site="trillion-ai-juku.com",

    passage=("In the end, it is curiosity, not talent, that decides "
             "how far a mind will travel."),

    # passage 由来ではない、説明用の英文 (すべて自塾の教材 rulehunt03 由来)
    en_examples=[
        "curiosity, not talent, decides how far a mind will travel",
        "It is tempting to believe that a book should be as easy as "
        "a friendly conversation.",
    ],

    # ★この vol は実在の入試問題を名乗らないので、裏の取れない主張は無い。
    unverified=[],

    # ★「実在の入試問題ではない」と打ち消している行。_is_claim は取りこぼさない側に
    #   倒してあるので打ち消し文も拾う。ここに書いて明示的に通す。
    disclaimers=["実在の入試問題ではありません"],

    editorial_notes=[
        "例文は自塾の教材 (scripts/eng_therules/rulehunt03/content.py) の原創文で、"
        "実在の入試問題ではない。1 枚目のチップでそう明示している。"
        "シリーズ名は「東大・京大の英文はこう読む」のままなので、"
        "誤解を招くと判断したら vol ごとに series を変えられる。",
        "「難関大で狙われる形」は頻度についての教育的な主張で、機械では裏を取れない。",
    ],

    caption=dict(
        full="""同じ “It is … that” でも、読み方は3通りあります。
外し方を知らないと、訳がまるごとねじれます。

例文: トリリオン作成のオリジナル (実在の入試問題ではありません)

━━━━━━━━━━━━━━━

In the end, it is curiosity, not talent,
that decides how far a mind will travel.

━━━━━━━━━━━━━━━

❌ ありがちな読み
「それは、心の行く先を決める“好奇心”というものである」
that を関係代名詞だと思うと、こうなります。
対比 (才能 ⇔ 好奇心) の焦点が消えて、ただの説明文になります。

⭕️ 正しい読み
「心がどこまで行くかを決めるのは、才能ではなく好奇心だ」

━━━━━━━━━━━━━━━

🔑 決め手は、たった1つの操作

It is と that を “外して” みる。

curiosity, not talent, decides how far a mind will travel

完全な文が残りました。だから強調構文です。

・外して文が残る → 強調構文「〜こそが」
・外して文が欠ける → 仮主語
・that の後ろが不完全 → 関係代名詞

━━━━━━━━━━━━━━━

💡 同じ形でも、こちらは違います

It is tempting to believe that a book should be as easy as
a friendly conversation.

外すと "tempting to believe" が宙に浮いて、文が成立しません。
こちらは仮主語の It です。

★覚えるのは「外して戻るか」だけ。
形が同じでも、戻るかどうかで役割が決まります。

━━━━━━━━━━━━━━━

📝 あなたは A と B、どちらで読みましたか?
コメントで教えてください。

🔖 保存して、長文で It is が出たときに見返してください。

📲 @trillion_ai
👉 trillion-ai-juku.com""",

        short="""同じ “It is … that” でも読み方は3通り。外し方を知らないと訳がねじれます。

例文: トリリオン作成のオリジナル (実在の入試問題ではありません)

In the end, it is curiosity, not talent,
that decides how far a mind will travel.

❌「それは、心の行く先を決める“好奇心”というものである」
⭕️「心がどこまで行くかを決めるのは、才能ではなく好奇心だ」

🔑 決め手は1つ。It is と that を “外して” みる。

curiosity, not talent, decides how far a mind will travel

完全な文が残る → 強調構文「〜こそが」
文が欠ける → 仮主語 / that の後ろが不完全 → 関係代名詞

📝 A と B、どちらで読みましたか? コメントで教えてください。
🔖 保存して、長文で It is が出たときに見返してください。

📲 @trillion_ai
👉 trillion-ai-juku.com""",

        hashtags=[
            "#大学受験", "#京大受験", "#東大受験", "#難関大", "#英文解釈",
            "#強調構文", "#英語長文", "#英文法", "#共通テスト", "#受験勉強",
            "#勉強垢", "#高校生勉強垢", "#浪人生", "#英語", "#英語学習",
            "#受験英語", "#早慶", "#国公立大学", "#関関同立", "#march",
            "#塾選び", "#オンライン塾", "#ai塾", "#AIコーチング", "#勉強法",
            "#高校生ママ", "#受験生親", "#トリリオンAIコーチング",
        ],
    ),

    slides=[
        # ── 1/6 表紙 ──────────────────────────────────────────────
        dict(n=1, align="center", blocks=[
            B("badge", "難関大で狙われる形"),
            B("gap", "m"),
            B("chip", "トリリオン作成のオリジナル例文"),
            B("gap", "m"),
            B("quote", [
                "In the end, it is curiosity, not talent,",
                "that decides how far a mind will travel.",
            ]),
            B("gap", "m"),
            B("bigq", "この [u]it[/u]、何者?"),
            B("gap", "s"),
            B("lead", "見抜けないと、訳が[p]まるごとねじれる。[/p]"),
            B("gap", "s"),
            B("gloss", "curiosity 好奇心 / talent 才能"),
            B("push"),
            B("cta", "▶ スワイプして挑戦"),
        ]),

        # ── 2/6 設問 ──────────────────────────────────────────────
        dict(n=2, align="top", blocks=[
            B("h", "Q. この [a]“It is … that”[/a]、どう読む?"),
            B("gap", "s"),
            B("dashbox_en", [
                "it is curiosity, not talent,",
                "[o]that[/o] decides how far",
                "a mind will travel",
            ]),
            B("gap", "s"),
            B("opts", [
                ("A.", "それは、心の行く先を決める\n「好奇心」というものである"),
                ("B.", "心がどこまで行くかを決めるのは、\n才能ではなく好奇心だ"),
            ]),
            B("gap", "s"),
            B("pill_pink", "直感でOK。AかBをコメントで!"),
            B("hint", "[a]It is[/a] と [a]that[/a] を外すとどうなる?"),
            B("push"),
            B("cta", "▶ 次のスライドで答え合わせ"),
            B("gap", "s"),
            B("source", "例文: トリリオン作成 (rulehunt03 訓練1)"),
        ]),

        # ── 3/6 解答 ──────────────────────────────────────────────
        dict(n=3, align="center", blocks=[
            B("eyebrow", "Answer"),
            B("gap", "s"),
            B("h", "正解は…"),
            B("gap", "s"),
            B("answer", "B"),
            B("gap", "m"),
            B("goodbox", "「心がどこまで行くかを決めるのは、\n才能ではなく[w]好奇心[/w]だ」"),
            B("gap", "s"),
            B("badbox", "[p]A[/p]で読むと、対比の焦点(才能 ⇔ 好奇心)が消えて\n"
                        "ただの説明文になる[!]"),
            B("gap", "m"),
            B("lead", "決め手は、[u]たった1つの操作。[/u]"),
            B("push"),
            B("cta", "▶ その操作へ"),
        ]),

        # ── 4/6 見分け方 ──────────────────────────────────────────
        dict(n=4, align="top", blocks=[
            B("h", "[a]It is[/a] と [a]that[/a] を[u]外して[/u]みる", sm=True),
            B("gap", "s"),
            B("rulebox", [
                "外して[w]文が残る[/w] → [p]強調構文[/p]「〜こそが」",
                "外して[w]文が欠ける[/w] → 仮主語・関係代名詞",
            ]),
            B("gap", "s"),
            B("fig", _diagram()),
            # ★.dashbox は white-space:nowrap。1 行に収まらない長さだと横へ溢れる
            #   (fit 検査が「右へ 123px」で落とした)。意図して折り返す。
            B("dashbox", "[s]curiosity, not talent,\n"
                         "decides how far a mind will travel[/s]"),
            B("gap", "s"),
            B("lead", "[p]完全な文が残った → 強調構文![/p]"),
            B("push"),
            B("cta", "▶ 見分けのもう一例"),
            B("gap", "s"),
            B("source", "例文: トリリオン作成 (rulehunt03 訓練1)"),
        ]),

        # ── 5/6 対比 ──────────────────────────────────────────────
        dict(n=5, align="center", blocks=[
            B("h", "同じ [a]It is[/a] でも、こちらは[p]違う[/p]"),
            B("gap", "m"),
            B("dashbox", "[s]It is tempting to believe that a book\n"
                         "should be as easy as a friendly conversation.[/s]"),
            B("gap", "m"),
            B("trans", "「本は気楽な会話のように易しいはずだ、と\n思いたくなる。」"),
            B("gap", "m"),
            B("notebar", "外すと[w]文が残らない[/w] → これは[p]仮主語[/p]の it"),
            B("gap", "m"),
            B("dashnote", "形が同じでも、[a]外して戻るかどうか[/a]で役割が決まる。\n"
                          "迷ったら、まず外してみること。", ctr=True),
            B("push"),
            B("cta", "▶ まとめへ"),
            B("gap", "s"),
            B("source", "例文: トリリオン作成 (rulehunt03 訓練2)"),
        ]),

        # ── 6/6 まとめ ────────────────────────────────────────────
        dict(n=6, align="top", blocks=[
            B("eyebrow", "まとめ"),
            B("gap", "s"),
            B("h", "[a]It is … that[/a] は「外して」決める"),
            B("gap", "m"),
            B("rulebox", [
                "外して[w]文が残る[/w] → 強調構文「〜こそが」",
                "外して[w]文が欠ける[/w] → 仮主語",
                "[a]that[/a] の後ろが不完全 → 関係代名詞",
                "強調構文は[p]対比[/p]とセットで来やすい",
            ]),
            B("gap", "m"),
            B("lead", "長文で It is が出たら、[u]まず外してみる。[/u]"),
            B("gap", "m"),
            B("dashnote", "保存して、次に It is … that が出たときに見返してください。\n"
                          "vol.03 も同じ形式で出します。", ctr=True),
            B("push"),
            B("cta", "▶ 保存 & フォローで vol.03 へ"),
        ]),
    ],
)
