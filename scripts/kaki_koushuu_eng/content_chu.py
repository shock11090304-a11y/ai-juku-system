# -*- coding: utf-8 -*-
"""中学生版（中3・高校受験）content。data/chu_*.json を読み込んで公開。"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name):
    with open(os.path.join(HERE, "data", name), encoding="utf-8") as f:
        return json.load(f)


META = {
    "series": "トリリオン夏期講習 英語",
    "level": "中学生版",
    "target": "中3・高校受験（難関私国立対応）",
    "minutes": 60,
    "grammar_dates": "7/27–31",
    "reading_dates": "8/17–21",
    "intro": "「文法はやったのに長文が読めない」を、この夏で終わらせる。前半は中学英文法の総点検を"
             "『ポイント整理 → 基礎問 → 標準 → 入試チャレンジ』の3段階で、後半は長文を"
             "『構造把握 → 論理 → 設問処理 → 速読 → 志望校別実戦』の順に1本ずつ鍛える全10回。",
    "kaisetsu_intro": "各問の解答と「なぜそうなるか（考え方）」を載せています。"
                      "まちがえた問題は解説を読み、翌日にもう一度解き直しましょう。",
}

GRAMMAR = [_load(f"chu_g{i}.json") for i in range(1, 6)]
READING = [_load(f"chu_r{i}.json") for i in range(1, 6)]
