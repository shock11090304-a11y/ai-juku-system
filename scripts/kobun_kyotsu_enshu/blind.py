# -*- coding: utf-8 -*-
"""盲検証用のデータを作る。正解・解説・現代語訳を伏せた「生徒が見るのと同じもの」を出す。

   ★解答は「①〜⑤の整数」で答えさせること（0始まりの添字で答えさせると全問ずれる。
     このリポジトリで何度も起きた事故）。blind.json にその指示を毎回書き出す。
"""
import json, os, re, glob

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "blind"); os.makedirs(OUT, exist_ok=True)
CIRC = "①②③④⑤"

def plain(s): return re.sub(r"\{\{/?[abcwxy]\}\}", "", s)

def mark(s):
    """傍線・波線を、紙で見えるのと同じ印に置きかえる"""
    for k, lab in (("a", "(ア)"), ("b", "(イ)"), ("c", "(ウ)"), ("x", "(Ａ)"), ("y", "(Ｂ)")):
        s = re.sub(r"\{\{" + k + r"\}\}(.*?)\{\{/" + k + r"\}\}", r"＿\1＿" + lab, s, flags=re.S)
    s = re.sub(r"\{\{w\}\}(.*?)\{\{/w\}\}", r"〜\1〜（波線部）", s, flags=re.S)
    return s

def main():
    key = {}
    for f in sorted(glob.glob(os.path.join(HERE, "sets", "set*.json"))):
        S = json.load(open(f, encoding="utf-8"))
        b = {
            "答え方": "各小問の答えは、選択肢の番号を 1〜5 の整数で書くこと（①＝1、⑤＝5）。0 から数えない。",
            "回": S["id"], "レベル": {1: "基礎", 2: "標準", 3: "本番"}[S["level_no"]],
            "出典": S["work"], "リード文": S["lead"],
            "本文": mark(S["passage"]),
            "注": [f'{i}　{n["word"]} ―― {n["gloss"]}' for i, n in enumerate(S["notes"], 1)],
            "設問": [],
        }
        for q in S["questions"]:
            for i, it in enumerate(q["items"]):
                b["設問"].append({
                    "設問番号": f'問{q["no"]}{it["label"]}',
                    "配点": q["points"],
                    "設問文": plain(q["text"]),
                    "選択肢": {str(j + 1): c for j, c in enumerate(it["choices"])},
                })
                key[f'第{S["id"]}回 問{q["no"]}{it["label"]}'] = it["answer"] + 1
        json.dump(b, open(os.path.join(OUT, os.path.basename(f)), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
    json.dump(key, open(os.path.join(HERE, "answer_key.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"blind/ に {len(glob.glob(os.path.join(OUT,'set*.json')))} 回分／小問 {len(key)} 個")
    print("鍵は answer_key.json（盲ソルバーには渡さない）")

if __name__ == "__main__":
    main()
