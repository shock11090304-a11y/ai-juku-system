# -*- coding: utf-8 -*-
"""語注の候補を洗い出し、data/gloss_targets.json に固定する (手元で回す道具。wordfreq と lemminflect が要る)。

    pip install wordfreq lemminflect
    python3 scripts/eiken_junichi/writing/gloss_scan.py

■ 何を「語注が要る語」とするか
  英文 (要約の本文・要約の解答例・意見論述の解答例) の語のうち、
    (1) 英語全体での出現頻度が低い (wordfreq の Zipf < THRESHOLD = 100万語あたり約2.5回未満) かつ
    (2) 準1級の語 (pre1_words.py) に入っていない
  もの。準1級の単語テスト・語彙問題の語は Zipf 中央値 3.50 (25%点 3.26) なので、
  それより明らかにまれな語 = 準1級の範囲を超える語、とみなす。
  ★ここで拾った語は、data の gloss (語注) に載せるか、gloss_skip に理由つきで載せる。
    check.py が gloss_targets.json と突き合わせて、どちらにも無い語があれば落とす。
  ★英文を直したら必ずこれを回し直す (check.py は英文のハッシュが変わると「回し直せ」で落ちる)。
"""
import glob
import hashlib
import json
import os
import sys

from lemminflect import getAllLemmas
from wordfreq import zipf_frequency

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pre1_words import TOK, forms, load_pre1  # noqa: E402

THRESHOLD = 3.4
PROPER = {"japan", "japanese", "led", "ai", "gps", "vr", "iss"}


def texts_of(d):
    s, e = d["summary"], d["essay"]
    return {"passage": " ".join(s["paras"]), "model": s["model"], "essay": " ".join(e["paras"])}


def sha(t):
    return hashlib.sha1(t.encode("utf-8")).hexdigest()


def rare_words(text, pre1):
    out = {}
    for t in TOK.findall(text):
        low = t.lower()
        if low in PROPER:
            continue
        lemmas = {low} | forms(low)
        for v in getAllLemmas(low).values():
            lemmas |= set(v)
        if lemmas & pre1:
            continue
        z = max(zipf_frequency(x, "en") for x in lemmas)
        if z < THRESHOLD:
            out[low] = round(z, 2)
    return out


def main():
    pre1 = load_pre1()
    data = {"threshold": THRESHOLD, "texts": {}}
    paths = [os.path.join(HERE, "data", "examples.json")] + sorted(glob.glob(os.path.join(HERE, "data", "set*.json")))
    for p in paths:
        d = json.load(open(p, encoding="utf-8"))
        tag = "EX" if p.endswith("examples.json") else f"S{d['no']}"
        for kind, text in texts_of(d).items():
            rare = rare_words(text, pre1)
            data["texts"][f"{tag}.{kind}"] = {"sha1": sha(text), "rare": sorted(rare)}
            print(f"{tag}.{kind:7s} " + ", ".join(f"{w}({z})" for w, z in sorted(rare.items(), key=lambda x: x[1])))
    with open(os.path.join(HERE, "data", "gloss_targets.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("WROTE data/gloss_targets.json")


if __name__ == "__main__":
    main()
