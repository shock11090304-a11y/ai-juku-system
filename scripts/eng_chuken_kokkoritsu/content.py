# -*- coding: utf-8 -*-
"""地方国公立・中堅大 英文法 実戦問題集 — 単一ソース。

組版・機械ゲート・盲検証は姉妹編と共有する（データだけがここにある）:
  WORKBOOK_DIR=scripts/eng_chuken_kokkoritsu python3 scripts/eng_kokkoritsu_nankan/build.py
"""
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from content_p1 import PART as P1  # noqa: E402
from content_p2 import PART as P2  # noqa: E402
from content_p3 import PART as P3  # noqa: E402

# 問題編に印字してよいフィールド（★ここに exp / point / ans / model を足さないこと。
# 足した瞬間に「答えが問題編に載る」＝知識ゼロで得点できる冊子になる）
Q_FIELDS = ("stem", "choices", "parts", "frame", "tokens", "ja", "src", "inst",
            "given", "hint", "context")

BOOK = {
    "title": "地方国公立・中堅大 英文法 実戦問題集",
    "sub": "四択／語句整序／空所補充／英文和訳／和文英訳",
    "series": "国公立難関大学コース（導入編）",
    "file": "地方国公立中堅大英文法_実戦問題集",
    "intro": [
        ("この問題集の位置づけ",
         "『難関国公立大 英文法 実戦問題集』の一段手前にあたる本です。"
         "四択から始めて、語句整序・記述の空所補充・英文和訳・和文英訳へと、"
         "同じ文法項目を少しずつ重い形で問い直していきます。"
         "第3部まで8割取れるようになったら、難関編の第1部へ進んでください。"),
        ("三部構成のねらい",
         "第1部（標準レベル）→ 第2部（中堅国公立レベル）→ 第3部（上位への橋渡し）と進みます。"
         "一文の長さと、一文の中で判断すべきことの数で難度が上がります。"
         "各部は100点満点で独立した一回分の演習です。時間を計って解いてください。"),
        ("解き方の約束",
         "①辞書を引かずに一度最後まで解く。②答え合わせのあと、間違えた問題の「▶ポイント」だけを"
         "ノートに書き写す。③一週間後にもう一度、同じ部を解き直す。"
         "四択で当たった問題も、なぜ他の三つが誤りなのかを言えるまでは「解けた」と数えません。"),
        ("採点のしかた",
         "四択・空所補充は解答と一致していれば正解です（解答編に併記した別解も可）。"
         "語句整序は語順が完全に一致していれば正解です。"
         "英文和訳と和文英訳の2つは、模範解答と一字一句同じである必要はありません。"
         "解答編に示した「採点のポイント」を1つ満たすごとに、英文和訳は2点、和文英訳は1点を"
         "与えてください（配点は各問の採点表に書いてあります）。"
         "ポイントは日本語のどの意味を落としていないかを見るもので、模範解答と同じ語句を"
         "使っている必要はありません。同じ内容が別の言い方で書けていれば加点してください。"),
        ("この問題集で扱う範囲",
         "本書は英文法・語法に特化しています。各部に掲げた大学名は、"
         "その大学の大問構成を再現したという意味ではなく、難易度の目安です。"
         "実際の入試では、これに加えて長文読解・自由英作文が課されます。"
         "本書はその土台となる「文を正確に組み立てる力」を鍛えるためのものです。"),
    ],
    "parts": [P1, P2, P3],
}

def _balance_mc():
    """四択の正解位置を stem の md5 順で機械的に散らす。
    ★手で番号を振ると必ず偏る（初版は34問中19問が2番に集中した）。
    解説は選択肢の番号を参照していないので、並べ替えても安全。"""
    mcs = [it for p in BOOK["parts"] for s in p["sections"]
           if s["kind"] == "mc" for it in s["items"]]
    order = sorted(range(len(mcs)),
                   key=lambda i: hashlib.md5(mcs[i]["stem"].encode()).hexdigest())
    for rank, i in enumerate(order):
        it = mcs[i]
        ch, a, target = it["choices"], it["ans"], rank % 4
        rest = ch[:a] + ch[a + 1:]
        it["choices"] = rest[:target] + [ch[a]] + rest[target:]
        it["ans"] = target


_balance_mc()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _workbook_gates import break_answer_runs  # noqa: E402
break_answer_runs(BOOK["parts"])


KIND_LABEL = {
    "mc": "四択",
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
