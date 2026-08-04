# -*- coding: utf-8 -*-
"""古文助動詞 完全演習プリント — 単一ソース。

組版・機械ゲート・盲検証は英文法問題集と共有する（データだけがここにある）:
  WORKBOOK_DIR=scripts/kobun_jodoushi python3 scripts/eng_kokkoritsu_nankan/build.py

★lang="ja" を立てると、英語専用のゲート（与えられた語の語幹照合・英単語数の下限）を
  スキップし、日本語向けの判定に切り替わる。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from content_p1 import PART as P1  # noqa: E402
from content_p2 import PART as P2  # noqa: E402
from content_p3 import PART as P3  # noqa: E402
from content_p4 import PART as P4  # noqa: E402
from tables import TABLES, FLOWS, STEPS  # noqa: E402

# 問題編に印字してよいフィールド（★ここに exp / point / ans / model を足さないこと。
# 足した瞬間に「答えが問題編に載る」＝知識ゼロで得点できる冊子になる）
Q_FIELDS = ("stem", "choices", "frame", "tokens", "ja", "src", "inst",
            "given", "hint", "context")

BOOK = {
    "title": "古文助動詞 完全演習プリント",
    "sub": "接続と活用／意味の判別／識別／古典本文での実戦",
    "series": "国語（古文）",
    "file": "古文助動詞_完全演習プリント",
    "lang": "ja",
    "intro": [
        ("この一冊で助動詞を終わらせる",
         "古文が読めない原因の大半は、助動詞が処理できていないことにあります。"
         "助動詞は数が三十ほどしかなく、しかも聞かれ方が決まっているので、"
         "順番どおりに演習すれば必ず終わります。"
         "第1部で形、第2部で意味、第3部で識別、第4部で実際の古典本文、"
         "という順に進んでください。"),
        ("なぜこの順番なのか",
         "意味を先に丸暗記しようとすると必ず挫折します。"
         "「む」に五つの意味があると覚えても、文中で選べないからです。"
         "先に「どの活用形につくか」を固めると、"
         "候補が二つか三つに絞られ、そこから意味を選ぶだけになります。"
         "識別問題も、接続を見れば半分は機械的に決まります。"),
        ("解き方の約束",
         "①まず傍線部の直前の語の活用形を言う。②接続から助動詞の候補を絞る。"
         "③主語・呼応の副詞・文脈で意味を決める。"
         "この三手順を、答えが分かっている問題でも省かないこと。"
         "手順を飛ばして当てた問題は、本番で外れます。"),
        ("採点のしかた",
         "四択・空所補充・文法的説明は、解答と一致していれば正解です"
         "（解答編に併記した別解も可）。"
         "現代語訳だけは模範解答と一字一句同じである必要はありません。"
         "解答編に示した「採点のポイント」を1つ満たすごとに2点を与えてください。"
         "ポイントは助動詞の意味を落としていないかを見るもので、"
         "模範解答と同じ言い回しである必要はありません。"),
        ("進め方（基本の確認→解説→基本問題→応用問題）",
         "各部の扉に「この部の解き方」を三手順で示してあります。"
         "解く前にその三手順を声に出して確認し、"
         "一問ごとに手順のどこで答えが決まったかを言えるようにしてください。"
         "答え合わせのときは、解答解説編の解説（なぜそうなるか）と"
         "▶ポイント（次に使える形）の二つを読みます。"),
        ("助動詞一覧表について",
         "接続表・活用表は、あえてこの問題編には載せていません。"
         "表が手元にあると、接続を問う設問を表から写すだけで解けてしまい、"
         "覚えたかどうかが分からなくなるからです。"
         "表と覚え方（語呂合わせ）、識別のフローチャートは、"
         "解答解説編の巻頭に「基本の確認」としてまとめてあります。"
         "解き終わってから、答え合わせと一緒に確認してください。"),
    ],
    # ★解答解説編の巻頭に置く「基本の確認」。問題編には絶対に出さない。
    "tables": TABLES,
    "flows": FLOWS,
    "parts": [P1, P2, P3, P4],
}

# 各部の解法手順（問題編の部扉に印字。手順だけなので答えは割れない）
for _p in BOOK["parts"]:
    _p["steps"] = STEPS[_p["no"]]

KIND_LABEL = {
    "mc": "四択",
    "fill": "記述",
    "jtrans": "現代語訳",
    "trans": "古文で書く",
    "error": "誤り指摘",
    "order": "語順整序",
    "rewrite": "書き換え",
}
# 採点要素で採る（唯一解が無い）出題形式
ELEMENT_KINDS = ("trans", "jtrans")


def all_items():
    """(part, section, item, 通し表示名) を順に返す。"""
    for p in BOOK["parts"]:
        for s in p["sections"]:
            for i, it in enumerate(s["items"], start=1):
                where = f'第{p["no"]}部 大問{s["no"]}-{i}'
                yield p, s, it, where


def frame_text():
    """問題編のうち「設問そのもの以外」＝表紙・前書き・部扉・大問見出し・指示文。"""
    buf = [BOOK["title"], BOOK["sub"]]
    for h, b in BOOK["intro"]:
        buf += [h, b]
    for p in BOOK["parts"]:
        buf += [p["level"], p["univ"], p["aim"]]
        for s in p["sections"]:
            buf += [s["title"], s["inst"]]
    return "\n".join(buf)


def question_text(exclude=None):
    """問題編に印字される全テキスト（解答漏洩ゲートの走査対象）。"""
    buf = [frame_text()]
    for p in BOOK["parts"]:
        for s in p["sections"]:
            for it in s["items"]:
                if it is exclude:
                    continue
                for f in Q_FIELDS:
                    v = it.get(f)
                    if isinstance(v, list):
                        buf += [str(x) for x in v]
                    elif v:
                        buf.append(str(v))
    return "\n".join(buf)
