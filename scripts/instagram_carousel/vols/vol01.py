# -*- coding: utf-8 -*-
"""vol.01 「東大・京大の英文はこう読む」— 京大 2023 の as (様態 vs みなす)。

★出所: 塾長が既に投稿した画像 6 枚のうち 1〜5 枚目を書き起こしたもの。
  6 枚目は提示が無かったので新規に起こした (まとめ + CTA)。
  出典表記と「大手予備校の模範解答が割れた」は**このリポジトリでは裏を取っていない**。
  だから unverified に宣言してある (宣言漏れは build_vol.verify が落とす)。
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from build_vol import B, rough_ellipse, squiggle  # noqa: E402
import theme_vol as T  # noqa: E402


# ── p4 の文構造図 ─────────────────────────────────────────────────────
# ★SVG に日本語を入れない。和文フォントが無い環境で豆腐になるため
#   (CLAUDE.md「✓/✗ は文字で置かず線で描く」と同じ理由)。和文は HTML 側に置く。
# ★x と幅を固定し textLength で強制する。Mac (ヒラギノ明朝/Georgia) と
#   Linux (DejaVu Serif) で字幅が違うので、成り行きに任せると注釈がずれる。
_WORDS = [
    # (語, x, 幅, 色) ─ 語間は 18px。as の丸囲みが前後の語に噛まない幅を取ってある。
    ("see",            14,  52, "#ffffff"),
    ("consciousness",  84, 206, "#ffffff"),
    ("as",            308,  38, T.AMBER),
    ("Louis",         364,  84, "#ffffff"),
    ("Armstrong",     466, 150, "#ffffff"),
    ("purportedly",   634, 176, T.MUTED),
    ("saw",           828,  54, "#ffffff"),
    ("jazz",          900,  64, "#ffffff"),
]


def _diagram():
    words = "".join(
        f'<text x="{x}" y="130" textLength="{w}" lengthAdjust="spacingAndGlyphs" '
        f'font-size="36" fill="{c}" font-family="Georgia,&quot;Liberation Serif&quot;,'
        f'&quot;DejaVu Serif&quot;,serif">{t}</text>'
        for t, x, w, c in _WORDS)

    ring = rough_ellipse(327, 118, 33, 32, rot=-5)
    sq_see = squiggle(14, 66, 150)
    sq_saw = squiggle(828, 882, 150)

    labels = "".join(
        f'<text x="{x}" y="192" font-size="34" font-weight="700" fill="{T.PINK}" '
        f'text-anchor="middle" font-family="Georgia,serif">{t}</text>'
        for t, x in (("S", 490), ("V", 855), ("O", 932)))

    return (
        '<svg width="850" viewBox="0 0 1000 285" fill="none" '
        'xmlns="http://www.w3.org/2000/svg">'
        '<defs>'
        f'<marker id="ar-a" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" '
        f'markerHeight="6" orient="auto-start-reverse">'
        f'<path d="M2 1L8 5L2 9" fill="none" stroke="{T.AMBER}" stroke-width="1.8" '
        f'stroke-linecap="round"/></marker>'
        f'<marker id="ar-p" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" '
        f'markerHeight="6" orient="auto-start-reverse">'
        f'<path d="M2 1L8 5L2 9" fill="none" stroke="{T.PINK}" stroke-width="1.8" '
        f'stroke-linecap="round"/></marker>'
        '</defs>'
        # 主節 see → as節 saw の「エコー」を示す点線アーチ
        f'<path d="M 34 86 C 260 22, 690 22, 848 78" stroke="{T.AMBER}" '
        f'stroke-width="3" stroke-dasharray="3 9" stroke-linecap="round" '
        f'marker-end="url(#ar-a)"/>'
        + words +
        f'<path d="{ring}" stroke="{T.PINK}" stroke-width="5" stroke-linecap="round"/>'
        f'<path d="{sq_see}" stroke="#ffffff" stroke-opacity="0.75" stroke-width="3" '
        f'stroke-linecap="round"/>'
        f'<path d="{sq_saw}" stroke="#ffffff" stroke-opacity="0.75" stroke-width="3" '
        f'stroke-linecap="round"/>'
        + labels +
        # as 節ぜんぶを囲む括弧 → 下向き矢印
        f'<path d="M 364 212 L 364 232 L 964 232 L 964 212" stroke="{T.PINK}" '
        f'stroke-width="3" stroke-linejoin="round"/>'
        f'<path d="M 664 232 L 664 272" stroke="{T.PINK}" stroke-width="3" '
        f'marker-end="url(#ar-p)"/>'
        '</svg>')


VOL = dict(
    key="vol01",
    series="東大・京大の英文はこう読む",
    label="vol.01",
    brand="TRILLION ENGLISH ACADEMY",
    handle="@trillion_ai",
    site="trillion-ai-juku.com",

    # ★正典の英文。全スライドの引用はここに実在しなければ verify が落とす。
    passage=("Such philosophers see consciousness as Louis Armstrong purportedly "
             "saw jazz: if you need to ask what it is, you're never going to know."),

    # passage 由来ではない、説明用の例文 (gate が英文の全数照合をするときの許可リスト)
    en_examples=["I see him as a rival.", "see A as B"],

    # ★機械では判定できない論点。ゲートが毎回そのまま印字して人手に回す。
    #   塾長の既発表分は勝手に書き換えないが、黙って通しもしない。
    editorial_notes=[
        "p4 の「as + S+V → 様態」は一般則としては狭い。自塾の教材 "
        "(scripts/eng_therules/rulehunt03/content.py) は「S+V なら様態・理由・時を文脈で」"
        "としている。この一文には効くが、規則として配るなら要調整。",
        "p4 の「as + 名詞 → とみなす」は (see A as B) の限定つきで初めて正しい。"
        "限定を外すと偽になる (as a result / work as a teacher)。",
        "p5 の見出し「後半は、プロでも割れた」は、割れた 2 案をスライドに出していない。"
        "主張を残すなら 2 案を並べる。出せないなら見出しを替える。",
        "p3 の訳「ジャズをそう見ていた…ように」の「そう」は、コロン以下を指すが "
        "そのスライドにコロン以下が載っていないので指示先が無い。",
        "コロン(=つまり)が前半と後半を繋いでいることを、どのスライドでも説明していない。",
    ],

    # ★機械では裏が取れない主張。宣言漏れも消し忘れも verify が落とす。
    unverified=[
        "実際の入試問題",
        "京都大学 2023年 英語 第2問",
        # ★該当しそうな記事は見つかるが、そこで扱われている下線部は
        #   この Armstrong の一文ではない可能性が高い (別問題の話の貼り替え)。
        "大手予備校の模範解答が割れた",
        "アームストロングの名言(とされる)",
    ],

    # ── 投稿文 (Instagram) ────────────────────────────────────────────
    # ★スライドと同じ vol に置く。文言が別ファイルに分かれると、
    #   画像だけ直して投稿文が古いまま、という事故が起きる。
    #   上限 2,200字 / ハッシュタグ 30個 はゲートが機械で見る。
    caption=dict(
        full="""“see A as B” だと思った瞬間、この一文は落ちます。
事故ポイントは、たった1語。

出典: 京都大学 2023年 英語 第2問 (下線部和訳)

━━━━━━━━━━━━━━━

Such philosophers see consciousness
as Louis Armstrong purportedly saw jazz:
if you need to ask what it is,
you're never going to know.

━━━━━━━━━━━━━━━

❌ よくある珍訳
「哲学者は、意識をルイ・アームストロングだと思っている」

see A as B =「AをBとみなす」を知っている人ほど、
as の直後にある Louis Armstrong を見た瞬間に、
そのまま「みなす」で組んでしまいます。

⭕️ 正しい読み
「ルイ・アームストロングがジャズをそう見ていた(と言われる)ように、
哲学者は意識を見ている」

━━━━━━━━━━━━━━━

🔑 見分けは as の“後ろ”だけ

・as + 名詞 →「〜として」
　(see A as B のときだけ「みなす」)
・as + S+V →「〜するように」(様態)。理由・時のこともある

ここでは as の後ろが
Louis Armstrong (S) + saw (V) + jazz (O) = 完全な節。
だから「みなす」ではなく様態です。

💡 もう一段の目印
主節の see と as節の saw が“エコー”しています。
同じ動詞が前後で響いていたら、様態のサイン。

★本当の判定条件はここ
「名詞が1つ見えたら」ではなく
「主語と動詞が揃って節になっているか」まで読むこと。
Louis Armstrong で目を止めると、そのまま誤答に落ちます。

━━━━━━━━━━━━━━━

コロン(:)は「つまり」。
後半が、前半の「そう見ていた」の中身です。

if you need to ask what it is, you're never going to know.
「それが何かを尋ねなければならないようなら、永遠にわからない。」

元ネタは“ジャズとは何かと聞くようじゃ、一生わからない”という
アームストロングの名言(とされる)。
だから purportedly(〜と言われる)が付いています。

━━━━━━━━━━━━━━━

📝 あなたは A と B、どちらで読みましたか?
コメントで教えてください。

🔖 保存して、長文で as が出たときに見返してください。
vol.02 でも、また1文を分解します。

📲 @trillion_ai
👉 trillion-ai-juku.com""",

        short="""“see A as B” だと思った瞬間、この一文は落ちます。

出典: 京都大学 2023年 英語 第2問 (下線部和訳)

Such philosophers see consciousness
as Louis Armstrong purportedly saw jazz

❌「意識をルイ・アームストロングだとみなしている」
⭕️「ルイ・アームストロングがジャズをそう見ていたように、意識を見ている」

🔑 見分けは as の“後ろ”だけ
・as + 名詞 →「〜として」(see A as B のときだけ「みなす」)
・as + S+V →「〜するように」(様態)。理由・時のことも

ここは Louis Armstrong (S) + saw (V) + jazz (O) で完全な節。
だから様態です。

💡 主節の see と as節の saw が“エコー”していたら様態のサイン。
名詞1つで止めず、節になっているかまで読むこと。

📝 A と B、どちらで読みましたか? コメントで教えてください。
🔖 保存して、長文で as が出たときに見返してください。

📲 @trillion_ai
👉 trillion-ai-juku.com""",

        hashtags=[
            "#大学受験", "#京大受験", "#東大受験", "#難関大", "#英文解釈",
            "#下線部和訳", "#英語長文", "#英文法", "#共通テスト", "#受験勉強",
            "#勉強垢", "#高校生勉強垢", "#浪人生", "#英語", "#英語学習",
            "#受験英語", "#早慶", "#国公立大学", "#関関同立", "#march",
            "#塾選び", "#オンライン塾", "#ai塾", "#AIコーチング", "#勉強法",
            "#高校生ママ", "#受験生親", "#トリリオンAIコーチング",
        ],
    ),

    slides=[
        # ── 1/6 表紙 ──────────────────────────────────────────────
        dict(n=1, align="center", blocks=[
            B("badge", "実際の入試問題"),
            B("gap", "m"),
            B("chip", "京都大学 2023年 英語 第2問(下線部和訳)"),
            B("gap", "m"),
            B("quote", [
                "“Such philosophers see consciousness",
                "as Louis Armstrong purportedly saw jazz:",
                "if you need to ask what it is,",
                "you’re never going to know.”",
            ]),
            B("gap", "m"),
            B("bigq", "この一文、[u]訳せる?[/u]"),
            B("gap", "s"),
            B("lead", "事故ポイントは、[p]たった1語。[/p]"),
            B("gap", "s"),
            B("gloss", "consciousness 意識 / purportedly 〜と言われる"),
            B("push"),
            B("cta", "▶ スワイプして挑戦"),
        ]),

        # ── 2/6 設問 ──────────────────────────────────────────────
        dict(n=2, align="top", blocks=[
            B("h", "Q. この [a]“as”[/a]、どう読む?"),
            B("gap", "m"),
            B("dashbox_en", [
                "see consciousness",
                "[o]as[/o] Louis Armstrong",
                "purportedly saw jazz",
            ]),
            B("gap", "m"),
            B("opts", [
                ("A.", "意識を「ルイ・アームストロング」とみなしている"),
                ("B.", "ルイ・アームストロングがジャズを見たように、\n意識を見ている"),
            ]),
            B("gap", "s"),
            B("pill_pink", "直感でOK。AかBをコメントで!"),
            B("gap", "s"),
            B("hint", "as の“後ろ”に何が来てる?"),
            B("push"),
            B("cta", "▶ 次のスライドで答え合わせ"),
            B("gap", "s"),
            B("source", "出典: 京都大学 2023年 英語 第2問"),
        ]),

        # ── 3/6 解答 ──────────────────────────────────────────────
        dict(n=3, align="center", blocks=[
            B("eyebrow", "Answer"),
            B("gap", "s"),
            B("h", "正解は…"),
            B("gap", "s"),
            B("answer", "B"),
            B("gap", "m"),
            B("goodbox", "「ルイ・アームストロングがジャズを\n"
                         "そう見ていた(と言われる)ように、意識を見ている」"),
            B("gap", "s"),
            B("badbox", "[p]A[/p]で読むと「哲学者は、意識をルイ・アームストロングだと\n"
                        "思っている」という[p]珍訳[/p]に"),
            B("gap", "m"),
            B("lead", "見分けるサインは、[u]たった1つ。[/u]"),
            B("push"),
            B("cta", "▶ そのサインへ"),
        ]),

        # ── 4/6 見分け方 ──────────────────────────────────────────
        dict(n=4, align="top", blocks=[
            B("h", "as の[u]“後ろ”[/u]を見れば、一発でわかる", sm=True),
            B("gap", "m"),
            B("rulebox", [
                "[a]as[/a] + [u]名詞[/u] → 「〜とみなす」 [m](see A as B)[/m]",
                "[a]as[/a] + [p]S+V[/p] → 「〜するように」 [m](様態)[/m]",
            ]),
            B("gap", "s"),
            B("fig", _diagram()),
            B("gap", "s"),
            B("lead", "[p]as の後ろに S+V → 様態![/p]"),
            B("gap", "s"),
            B("dashnote", "主節の [a]see[/a] と as節の [a]saw[/a] が[a]“エコー”[/a]していたら\n"
                          "様態のサイン", ctr=True),
            B("gap", "s"),
            B("dashnote", "[s]I see him as [u]a rival[/u].[/s]　→　"
                          "as の後ろが[u]名詞[/u] =「みなす」", ctr=True),
            B("push"),
            B("cta", "▶ 後半には“もう一つの仕掛け”"),
            B("gap", "s"),
            B("source", "出典: 京都大学 2023年 英語 第2問"),
        ]),

        # ── 5/6 後半 ──────────────────────────────────────────────
        dict(n=5, align="center", blocks=[
            B("h", "後半は、プロでも[p]割れた[/p]"),
            B("gap", "m"),
            B("quote", [
                "if you need to ask what it is,",
                "you’re never going to know.",
            ], sm=True),
            B("gap", "m"),
            B("trans", "「それが何かを尋ねなければならないようなら、\n永遠にわからない。」"),
            B("gap", "m"),
            B("notebar", "実はこの後半、[u]大手予備校の模範解答が割れた[/u]部分。"),
            B("gap", "m"),
            B("dashnote", "元ネタは“ジャズとは何かと聞くようじゃ、一生わからない”という\n"
                          "アームストロングの名言(とされる)。だから\n"
                          "[a]purportedly[/a](〜と言われる)が付いている。"),
            B("push"),
            B("cta", "▶ まとめへ"),
            B("gap", "s"),
            B("source", "出典: 京都大学 2023年 英語 第2問"),
        ]),

        # ── 6/6 まとめ (★提示画像に無かったので新規に起こした) ────
        dict(n=6, align="top", blocks=[
            B("eyebrow", "まとめ"),
            B("gap", "s"),
            B("h", "as は「後ろ」で決まる"),
            B("gap", "m"),
            # ★ここは提示画像に無く新規に起こした側。p4 の「(see A as B)」という
            #   限定を落とすと端的に偽になる (as+名詞 の大多数は「として」)。
            #   自塾の教材 scripts/eng_therules/rulehunt03/content.py の正典
            #   「as は後ろ次第 —— 名詞なら「として」、S+V なら様態・理由・時を文脈で」
            #   に合わせてある。
            B("rulebox", [
                "[a]as[/a] + [u]名詞[/u] → 「〜として」",
                "[a]as[/a] + [p]S+V[/p] → 様態・理由・時",
                "[a]see A as B[/a] のときだけ「〜とみなす」",
                "動詞が[a]エコー[/a]していたら様態",
            ]),
            B("gap", "m"),
            B("lead", "長文で as が出たら、[u]まず後ろを見る。[/u]"),
            B("gap", "m"),
            B("dashnote", "保存して、次に as が出てきたときに見返してください。\n"
                          "vol.02 も同じ形式で出します。", ctr=True),
            B("push"),
            B("cta", "▶ 保存 & フォローで vol.02 へ"),
        ]),
    ],
)
