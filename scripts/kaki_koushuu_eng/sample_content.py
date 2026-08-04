# -*- coding: utf-8 -*-
"""レンダリング検証用サンプル（全問題型を1つずつ含む）。本番は content_chu / content_kou。"""

META = {
    "series": "トリリオン夏期講習 英語",
    "level": "サンプル版",
    "target": "レンダリング検証",
    "minutes": 60,
    "grammar_dates": "7/27–31",
    "reading_dates": "8/17–21",
    "intro": "全問題型が字化けなく組版されるかを確認するためのダミー。",
}

GRAMMAR = [
    {
        "no": 1, "date": "7/27",
        "title": "be動詞・一般動詞・時制",
        "goal": "be動詞と一般動詞を混同せず、現在・過去・進行形を正しく使い分ける。",
        "points": [
            {"h": "be動詞と一般動詞は「一文に一つ」", "body": "be動詞（am/is/are）は「＝（イコール）」、一般動詞（play, likeなど）は「動作」。両方をいっしょに並べない。",
             "ex": [["She is a student.", "彼女は生徒だ。"], ["She plays tennis.", "彼女はテニスをする。"]],
             "rule": "be動詞の否定は not、一般動詞の否定は don't/doesn't。"},
            {"h": "過去形と過去進行形", "body": "過去形は「終わった動作」、過去進行形 was/were ~ing は「そのときやっている最中だった動作」。",
             "ex": [["I watched TV.", "私はテレビを見た。"], ["I was watching TV then.", "そのとき見ている最中だった。"]]},
        ],
        "kiso": [
            {"type": "fill", "stem": "My brother ______ soccer every Sunday. (play)", "ans": "plays",
             "point": "3単現の s", "exp": "主語 my brother は3人称単数なので、一般動詞に s を付けて plays。"},
            {"type": "mc", "stem": "They ______ in the library now.", "choices": ["is", "are", "am", "be"], "ans": 1,
             "point": "be動詞の一致", "exp": "主語 They は複数なので are。"},
        ],
        "hyojun": [
            {"type": "mc", "stem": "I ______ my homework when my mother came home.",
             "choices": ["do", "did", "was doing", "am doing"], "ans": 2,
             "point": "過去進行形", "exp": "「帰宅したとき、〜している最中だった」は過去進行形 was doing。"},
            {"type": "order", "ja": "私は昨日、公園で走っていました。",
             "tokens": ["running", "I", "in the park", "was", "yesterday"],
             "ans": "I was running in the park yesterday",
             "point": "過去進行形の語順", "exp": "was + ~ing の後ろに場所・時を続ける。"},
            {"type": "rewrite", "given": "Ken is a good tennis player.",
             "target": "Ken ______ tennis very ______.", "blanks": ["plays", "well"],
             "point": "名詞→動詞の言い換え", "exp": "「上手なテニス選手」＝「テニスを上手にする」。plays well。"},
        ],
        "nyushi": [
            {"type": "error",
             "html": "[a|When] I [b|was] young, I [c|am] [d|interested] in insects.",
             "ans": "c", "correct": "am → was",
             "point": "時制の一致", "exp": "文全体が過去（When I was young）なので am ではなく was。"},
            {"type": "ja2en", "ja": "私の姉は今、宿題をしています。",
             "models": ["My sister is doing her homework now.", "My older sister is doing her homework right now."],
             "point": "現在進行形 is ~ing", "mistakes": "does と混同しない。now があるので進行形。"},
        ],
    },
]

READING = [
    {
        "no": 1, "date": "8/17",
        "title": "構造把握（英文解釈）",
        "goal": "1文の骨組み（主語S・動詞V）を見抜き、長い文でも意味の中心を掴む。",
        "points": [
            {"h": "まず主語(S)と動詞(V)を探す", "body": "英語の文は S が「だれが」、V が「どうする」。修飾語をかっこに入れて、SV だけ先に取り出すと文が読める。",
             "ex": [["The boy (in the red cap) runs fast.", "（赤い帽子の）少年が速く走る。"]],
             "rule": "主語のあとの最初の動詞が、その文の中心 V。"},
        ],
        "passage": {
            "title": "The Power of Small Habits", "jtitle": "小さな習慣の力",
            "paras": [
                ["Many people believe that big changes need big actions.",
                 "However, small habits often matter more than dramatic decisions.",
                 "A student who reads only ten pages a day finishes many books in a year."],
                ["The secret is not effort on a single day but repetition over time.",
                 "Because small actions feel easy, we can continue them without stress.",
                 "In this way, tiny steps quietly build a very different future."],
            ],
            "trans": {
                "1": "多くの人は、大きな変化には大きな行動が必要だと信じている。",
                "2": "しかし、小さな習慣は劇的な決断よりも大切であることが多い。",
                "3": "1日にたった10ページ読む生徒は、1年で多くの本を読み終える。",
                "4": "秘訣は、ある1日の努力ではなく、時間をかけた繰り返しである。",
                "5": "小さな行動は楽に感じられるので、私たちはストレスなく続けられる。",
                "6": "このようにして、小さな一歩が静かにまったく違う未来を築く。",
            },
        },
        "vocab": [
            ["dramatic", "形", "劇的な"], ["repetition", "名", "繰り返し"],
            ["effort", "名", "努力"], ["quietly", "副", "静かに"],
        ],
        "questions": [
            {"type": "rc_mc", "q": "文(2)で筆者が最も伝えたいことはどれか。",
             "choices": ["大きな決断が最も重要だ", "小さな習慣が大きな決断より大切なことが多い", "習慣は変えられない", "本を読む必要はない"],
             "ans": 1, "exp": "However で前文を否定し、small habits ... matter more と述べている。"},
            {"type": "rc_desc", "q": "文(4)の主語(S)と動詞(V)をそれぞれ抜き出しなさい。",
             "ans": "S = The secret／V = is", "exp": "not A but B（AではなくB）は補語の中身。文の中心の V は is。", "lines": 1},
        ],
    },
]
