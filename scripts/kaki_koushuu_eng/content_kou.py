# -*- coding: utf-8 -*-
"""高校生版（大学受験）content。data/kou_*.json を読み込んで公開。"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name):
    with open(os.path.join(HERE, "data", name), encoding="utf-8") as f:
        return json.load(f)


META = {
    "series": "トリリオン夏期講習 英語",
    "level": "高校生版",
    "target": "大学受験（共通テスト〜MARCH・中堅国公立）",
    "minutes": 75,
    "grammar_dates": "7/27–31",
    "reading_dates": "8/17–21",
    "intro": "「文法はやったのに長文が読めない」を、この夏で終わらせる。前半は英文法を"
             "『文型 → 時制・態・助動詞 → 準動詞 → 関係詞・接続詞・比較 → 仮定法・倒置・省略』と"
             "体系整理（ポイント整理 → 基礎問 → 標準 → 入試チャレンジ）、後半は長文を"
             "『構造把握 → 論理展開 → 設問処理 → 速読 → 志望校別実戦』で鍛える全10回。",
    "kaisetsu_intro": "各問の解答と考え方（核心の一言 → なぜ → 原則化）を載せています。"
                      "まちがえた問題は解説を読み、翌日に解き直して『使える文法』にしましょう。",
}

GRAMMAR = [_load(f"kou_g{i}.json") for i in range(1, 6)]
READING = [_load(f"kou_r{i}.json") for i in range(1, 6)]
