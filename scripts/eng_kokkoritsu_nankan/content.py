# -*- coding: utf-8 -*-
"""難関国公立大 英文法 実戦問題集 — 単一ソース（format 非依存）。

build.py（PDF 組版）と check.py（機械ゲート）がこの BOOK だけを読む。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from content_p1 import PART as P1  # noqa: E402
from content_p2 import PART as P2  # noqa: E402
from content_p3 import PART as P3  # noqa: E402

# 問題編に印字してよいフィールド（★ここに exp / point / fix / ans / model を足さないこと。
# 足した瞬間に「答えが問題編に載る」＝知識ゼロで得点できる冊子になる）
Q_FIELDS = ("stem", "parts", "frame", "tokens", "ja", "src", "inst", "given", "hint", "context")

BOOK = {
    "title": "難関国公立大 英文法 実戦問題集",
    "sub": "誤り指摘／語句整序／空所補充／英文和訳／和文英訳",
    "series": "国公立難関大学コース",
    "file": "難関国公立英文法_実戦問題集",
    "intro": [
        ("この問題集がふつうの文法問題集と違うところ",
         "難関国公立大の二次試験は、私立大のような四択の文法問題をほとんど出しません。"
         "文法力は「誤りを見抜く」「語順を組み立てる」「英文の構造を読み解いて訳す」"
         "「日本語を英語の型に載せ替える」という形で試されます。"
         "本書はその問われ方を再現しています。"
         "四択に慣れた人ほど最初は手が止まりますが、それが本番の手ざわりです。"),
        ("三部構成のねらい",
         "第1部（上位国公立レベル）→ 第2部（旧帝大レベル）→ 第3部（最難関レベル）と進みます。"
         "難度は一文の長さと構文の入れ子の深さで上がっていきます。"
         "各部は100点満点で独立した一回分の演習です。時間を計って解いてください。"),
        ("解き方の約束",
         "①辞書を引かずに一度最後まで解く。②答え合わせのあと、間違えた問題の「▶ポイント」だけを"
         "ノートに書き写す。③一週間後にもう一度、同じ部を解き直す。"
         "文法は「知っている」から「使える」までの距離が長い分野です。二度解いて初めて身につきます。"),
        ("採点のしかた",
         "誤り指摘・空所補充は解答と一致していれば正解です（解答編に併記した別解も可）。"
         "語句整序は語順が完全に一致していれば正解です。"
         "英文和訳と和文英訳の2つは、模範解答と一字一句同じである必要はありません。"
         "解答編に示した「採点のポイント」を1つ満たすごとに、英文和訳は2点、和文英訳は1点を"
         "与えてください（配点は各問の採点表に書いてあります）。"
         "ポイントは日本語のどの意味を落としていないかを見るもので、模範解答と同じ語句を"
         "使っている必要はありません。同じ内容が別の言い方で書けていれば加点してください。"),
        ("この問題集で扱う範囲",
         "本書は英文法・語法に特化しています。各部に掲げた大学名は、"
         "その大学の大問構成を再現したという意味ではなく、**難易度の目安**です。"
         "実際の二次試験では、これに加えて長文読解・要約・自由英作文が課されます"
         "（自由英作文は本書が挙げたほぼ全ての大学が毎年出します）。"
         "本書はその土台となる「文を正確に組み立てる力」を鍛えるためのもので、"
         "一回分の入試問題を丸ごと再現したものではありません。"),
    ],
    "parts": [P1, P2, P3],
}

KIND_LABEL = {
    "error": "誤り指摘",
    "order": "語句整序",
    "fill": "空所補充",
    "rewrite": "書き換え",
    "jtrans": "英文和訳",
    "trans": "和文英訳",
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
    """問題編のうち「設問そのもの以外」＝表紙・前書き・部扉・大問見出し・指示文。
    ここに文法項目名が出ると、その大問が何の文法かが割れる。"""
    buf = [BOOK["title"], BOOK["sub"]]
    for h, b in BOOK["intro"]:
        buf += [h, b]
    for p in BOOK["parts"]:
        buf += [p["level"], p["univ"], p["aim"]]
        for s in p["sections"]:
            buf += [s["title"], s["inst"]]
    return "\n".join(buf)


def question_text(exclude=None):
    """問題編に印字される全テキスト（解答漏洩ゲートの走査対象）。
    exclude に item を渡すと、その設問自身の文だけを除いて返す
    （書き換え問題の解答が元の文と語を共有するのは当然なので、そこは漏洩ではない）。"""
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
