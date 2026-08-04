# -*- coding: utf-8 -*-
"""化学(理論)総復習トレーニングの内容を parts_private/*.json から読み込む。

数学の content_kiso2.py と同じ形(PARTS / PART_POINTS)に整形して build_chem.py に渡す。
JSON を単一ソースにしているのは、作問→独立盲解答→照合のワークフローが
ファイルを直接書き換えるため(Python に直書きすると照合の修正が反映できない)。
"""
import os, re, json

HERE = os.path.dirname(os.path.abspath(__file__))
PRIV = os.path.join(HERE, "parts_private")

# 各編の「攻略の手順」(扉ページの枠)。json の overview をそのまま使う。
PART_POINTS = {}
PARTS = []

for n in range(1, 7):
    path = os.path.join(PRIV, f"part{n}.json")
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    # 編名の「第3編 化学反応とエネルギー」/「第1編　気体と液体」の空白幅も編ごとに揺れていたので全角に統一
    area = re.sub(r"^(第\d編)\s*", r"\1　", d["area"])
    # ★編によって単元名が「状態変化と熱量【融解・蒸発／加熱曲線】」と【】付きだったり
    #   素の「気体の法則と状態方程式」だったりで揺れていた(作問を並列で回した副作用)。
    #   【】の中身は tag 欄に別途出るので、単元名からは落として冊子内で表記を揃える。
    for u in d["units"]:
        u["name"] = u["name"].split("【")[0].strip()
    # ★編扉の副題。以前は u["tag"](作問管理用スラッグ)を並べていたため、生徒に配る紙に
    #   「boyle-charles-ideal-gas ／ partial-pressure-mixture」がそのまま印刷されていた。
    #   しかも 07〜09 の tag だけ日本語で、編ごとに体裁も揃っていなかった。単元名を並べる。
    PARTS.append({"area": area, "sub": " ／ ".join(u["name"] for u in d["units"]),
                  "units": d["units"]})
    PART_POINTS[area] = d.get("overview", "")


def all_units():
    return [u for p in PARTS for u in p["units"]]


def total_q():
    return sum(len(u["problems"]) for u in all_units())
