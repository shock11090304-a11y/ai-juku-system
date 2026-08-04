#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""passages/*.json のスキーマ揺れを正規化する(冪等)。

10本を別々のエージェントに並列で書かせたので、同じ意味のフィールドが題ごとに違う形になった:
  - glossary のキー … "ja" と "meaning_ja" が混在
  - distractor_ja  … 文字列 / 選択肢番号をキーにした dict / 4要素の list が混在
そのままだと verify は AttributeError、build は dict の repr を紙に印刷する。
**単一ソース側を1回そろえる**(読み手ごとに場当たり対応を入れない)。
"""
import os, json, glob, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CIRCLED = "①②③④"


def to_str(dj, answer):
    """distractor_ja を「①… ②… ③…」の1つの文字列にする(正解の番号は飛ばす)。"""
    if isinstance(dj, str):
        return dj.strip()
    parts = []
    if isinstance(dj, dict):
        for k, v in sorted(dj.items(), key=lambda kv: str(kv[0])):
            try:
                i = int(k)
            except ValueError:
                parts.append(str(v))
                continue
            if i == answer:                      # 正解の説明は explanation_ja 側にある
                continue
            parts.append(f"{CIRCLED[i-1]}{v}")
    elif isinstance(dj, list):
        for i, v in enumerate(dj, 1):
            if i == answer or not str(v).strip() or str(v).strip() == "正解。":
                continue
            parts.append(f"{CIRCLED[i-1]}{v}")
    return "　".join(parts)


def main():
    changed = 0
    for p in sorted(glob.glob(os.path.join(HERE, "passages", "p*.json"))):
        d = json.load(open(p, encoding="utf-8"))
        before = json.dumps(d, ensure_ascii=False, sort_keys=True)

        for g in d.get("glossary") or []:
            if "ja" not in g and "meaning_ja" in g:
                g["ja"] = g.pop("meaning_ja")

        for q in d["questions"]:
            q["distractor_ja"] = to_str(q.get("distractor_ja"), q.get("answer"))
            if not isinstance(q.get("explanation_ja"), str):
                q["explanation_ja"] = str(q.get("explanation_ja"))

        if json.dumps(d, ensure_ascii=False, sort_keys=True) != before:
            json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            changed += 1
            print(f"  正規化: {os.path.basename(p)}")
    print(f"{changed} ファイルを正規化")


if __name__ == "__main__":
    sys.exit(main())
