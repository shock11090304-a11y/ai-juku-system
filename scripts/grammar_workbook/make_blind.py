#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""units/*.json から「正解・解説を伏せた」盲検証用ファイルを units_blind/ に生成する。

盲ソルバー(検証エージェント)はこのファイルだけを見て解くため、answer_index /
answer_text / explanation / point は一切含めない。
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "units")
DST = os.path.join(HERE, "units_blind")
os.makedirs(DST, exist_ok=True)

def blind_q(q):
    t = q["type"]
    b = {"no": q["no"], "type": t}
    if t == "mc":
        b["stem"] = q["stem"]
        b["choices"] = q["choices"]
    elif t == "order":
        b["prompt_ja"] = q.get("prompt_ja", "")
        b["tokens"] = q.get("tokens", [])
    elif t == "rewrite":
        b["original"] = q.get("original", "")
        b["instruction"] = q.get("instruction", "")
    return b

def main():
    only = None  # 特定slugのみ再生成したい場合に使用 (Noneで全件)
    import sys
    if len(sys.argv) > 1:
        only = set(sys.argv[1:])
    n = 0
    for fn in sorted(os.listdir(SRC)):
        if not fn.endswith(".json"):
            continue
        slug = fn[:-5]
        if only and slug not in only:
            continue
        d = json.load(open(os.path.join(SRC, fn), encoding="utf-8"))
        out = {"unit": d["unit"], "unit_slug": d.get("unit_slug", slug),
               "questions": [blind_q(q) for q in d["questions"]]}
        json.dump(out, open(os.path.join(DST, fn), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        n += 1
    print(f"blind files written: {n} -> {DST}")

if __name__ == "__main__":
    main()
