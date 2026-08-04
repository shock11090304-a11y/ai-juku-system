# -*- coding: utf-8 -*-
"""盲ソルバー検証用: data/*.json から正解を除去した blind_all.json と、
照合用 answer_key.json を出力する。独立エージェントは blind だけを見て解く。
"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

p1 = json.load(open(os.path.join(DATA, "part1_vocab.json"), encoding="utf-8"))
p2 = json.load(open(os.path.join(DATA, "part2_cloze.json"), encoding="utf-8"))
p3 = json.load(open(os.path.join(DATA, "part3_reading.json"), encoding="utf-8"))

blind = {"daimon1": [], "daimon2": [], "daimon3": []}
key = {}

for it in p1["items"]:
    blind["daimon1"].append({"key": it["id"], "sentence": it["sentence"], "choices": it["choices"]})
    key[it["id"]] = it["answer"]

for pa in p2["passages"]:
    bl = {"id": pa["id"], "title": pa["title"], "text": pa["text"], "blanks": []}
    for b in pa["blanks"]:
        k = "%s_b%s" % (pa["id"], b["n"])
        bl["blanks"].append({"key": k, "n": b["n"], "choices": b["choices"]})
        key[k] = b["answer"]
    blind["daimon2"].append(bl)

for pa in p3["passages"]:
    bl = {"id": pa["id"], "title": pa["title"], "paragraphs": pa["paragraphs"], "questions": []}
    for i, q in enumerate(pa["questions"], 1):
        k = "%s_q%d" % (pa["id"], i)
        bl["questions"].append({"key": k, "q": q["q"], "choices": q["choices"]})
        key[k] = q["answer"]
    blind["daimon3"].append(bl)

json.dump(blind, open(os.path.join(HERE, "blind_all.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
json.dump(key, open(os.path.join(HERE, "answer_key.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("blind: 大問1=%d 大問2=%d 大問3=%d (計%d問)" % (
    len(blind["daimon1"]),
    sum(len(x["blanks"]) for x in blind["daimon2"]),
    sum(len(x["questions"]) for x in blind["daimon3"]),
    len(key)))
