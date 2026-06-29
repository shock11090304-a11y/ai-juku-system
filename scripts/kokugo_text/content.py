# -*- coding: utf-8 -*-
"""国語テキスト（現古漢統合）コンテンツの単一ソース。

HTML（kokugo-nankan.html）と PDF（kokugo-nankan.pdf）の両方を
このモジュールから生成し、内容のドリフトを防ぐ。
"""

from content_gendai import GENDAI
from content_kobun import KOBUN
from content_kanbun import KANBUN

TITLE = "国公立難関 国語"
SUBTITLE = "現代文・古文・漢文 ── 偏差値50から65へ"
TAGLINE = "『型』で読み、『手順』で解き、『要素』で書く"
EDITIONS = [GENDAI, KOBUN, KANBUN]

COURSE_INTRO = (
    "本書は、国公立難関大学の国語（現代文・古文・漢文）で、"
    "偏差値50の段階から偏差値65到達を目指すための、再現性のある『型』を集めたコース教材です。"
    "才能や読書量ではなく、大手予備校が体系として教える『読み方・解き方・書き方の手順』を、"
    "そのまま身につけられるように構成しました。各編は〔講義（型）→例題→確認問題→演習〕の順で進みます。"
)

HOW_TO_USE = [
    "まず各講の『重要ポイント枠（型）』を覚える。ここが得点の核です。",
    "例題は手順どおりに自分で手を動かしてから答えを開くこと。",
    "確認問題（4択）で型が使えているかを即チェックする。",
    "各編の最後の『演習』は、本番の二次記述を想定。模範解答だけでなく"
    "『採点ルーブリック（部分点の付き方）』で自己採点する。",
    "記述は『要素を数えて、本文の言葉で、必要な数だけ』。これを全問で徹底する。",
]


def counts():
    """編ごとの講数・例題数・確認問題数・演習設問数を数える（表紙/目次用）。"""
    out = []
    for ed in EDITIONS:
        n_lessons = len(ed["lessons"])
        n_quiz = n_ex = 0
        for ls in ed["lessons"]:
            for b in ls["blocks"]:
                if b["t"] == "quiz":
                    n_quiz += 1
                elif b["t"] == "example":
                    n_ex += 1
        n_drill = len(ed["drill"]["questions"])
        out.append({
            "key": ed["key"], "label": ed["label"],
            "lessons": n_lessons, "examples": n_ex,
            "quizzes": n_quiz, "drill_q": n_drill,
        })
    return out
