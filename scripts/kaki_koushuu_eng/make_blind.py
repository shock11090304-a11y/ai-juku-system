# -*- coding: utf-8 -*-
"""
data/<key>.json から「解答を伏せた」blind/<key>.json を作る（ブラインド採点用）。
閉じた形式（mc/fill/order/error/rewrite/rc_mc）のみ items に載せる。
ja2en / rc_desc は自由記述なので別途クリティックが品質検査する。

  python3 make_blind.py            # data/*.json すべて
"""
import json, os, glob

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
BLIND = os.path.join(HERE, "blind")
os.makedirs(BLIND, exist_ok=True)

TIER_PREFIX = {"kiso": "kiso", "hyojun": "hyojun", "nyushi": "nyushi"}


def blind_grammar_item(iid, q):
    t = q["type"]
    base = {"id": iid, "type": t}
    if t == "mc":
        base.update(stem=q.get("stem"), note=q.get("note"), choices=q.get("choices"))
    elif t == "fill":
        base.update(stem=q.get("stem"), note=q.get("note"))
    elif t == "order":
        base.update(ja=q.get("ja"), tokens=q.get("tokens"))
    elif t == "error":
        base.update(html=q.get("html"))
    elif t == "rewrite":
        base.update(given=q.get("given"), target=q.get("target"))
    else:
        return None  # ja2en は自由記述
    return base


def blind_reading_item(iid, q):
    if q["type"] == "rc_mc":
        return {"id": iid, "type": "rc_mc", "q": q.get("q"), "choices": q.get("choices")}
    return None  # rc_desc は自由記述


def build_blind(path):
    key = os.path.basename(path)[:-5]
    d = json.load(open(path, encoding="utf-8"))
    out = {"key": key, "kind": "grammar" if key.split("_")[1].startswith("g") else "reading", "items": []}
    if out["kind"] == "grammar":
        for tier in ("kiso", "hyojun", "nyushi"):
            for i, q in enumerate(d.get(tier, []), start=1):
                it = blind_grammar_item(f"{tier}{i}", q)
                if it:
                    out["items"].append(it)
    else:
        pas = d.get("passage", {})
        out["passage"] = {"title": pas.get("title"), "jtitle": pas.get("jtitle"), "paras": pas.get("paras")}
        for i, q in enumerate(d.get("questions", []), start=1):
            it = blind_reading_item(f"q{i}", q)
            if it:
                out["items"].append(it)
    with open(os.path.join(BLIND, key + ".json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    return key, len(out["items"])


def main():
    files = sorted(glob.glob(os.path.join(DATA, "*.json")))
    for p in files:
        k, n = build_blind(p)
        print(f"blind {k}: {n} closed-form items")
    print(f"total {len(files)} files")


if __name__ == "__main__":
    main()
