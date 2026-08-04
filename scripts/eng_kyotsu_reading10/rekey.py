#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""正解番号の配置を組み替える(選択肢を入れ替えて answer を変える)。

なぜ: 最初に配った正解番号が、10題すべてで「問1〜問4の正解が①②③④の並べ替え」に
なっていた。3問確信できれば4問目が消去法で決まってしまう(本文を読まずに1問取れる)。
題内での重複を許す配置に組み替える。全体の①②③④の均衡は保つ。

やること: 各問で options[old-1] と options[new-1] を入れ替え、answer を new にする。
distractor_ja は「①…②…④…」の形で番号を参照しているので、ラベルも同じ規則で入れ替える。
"""
import os, re, json, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
CIRCLED = "①②③④"

# (題, 問) → 新しい正解番号。書いていない問は変更しない。
NEWKEY = {
    (1, 4): 1, (1, 5): 3,
    (2, 4): 4, (2, 5): 2,
    (3, 3): 3, (3, 5): 2,
    (4, 3): 2,
    (5, 4): 4,
    (6, 4): 3,
    (7, 3): 2, (7, 5): 3,
    (8, 3): 3,
    (9, 3): 1,
    (10, 4): 2, (10, 5): 3,
}


def swap_labels(text, a, b):
    """distractor_ja 内の丸数字ラベル a↔b を入れ替える(1始まり)。"""
    if not text:
        return text
    ca, cb = CIRCLED[a - 1], CIRCLED[b - 1]
    return text.replace(ca, "\x00").replace(cb, ca).replace("\x00", cb)


def main():
    changed = 0
    for no in range(1, 11):
        p = os.path.join(HERE, "passages", f"p{no:02d}.json")
        d = json.load(open(p, encoding="utf-8"))
        touched = False
        for i, q in enumerate(d["questions"], 1):
            new = NEWKEY.get((no, i))
            if not new or new == q["answer"]:
                continue
            old = q["answer"]
            opts = q["options"]
            opts[old - 1], opts[new - 1] = opts[new - 1], opts[old - 1]
            q["answer"] = new
            q["distractor_ja"] = swap_labels(q.get("distractor_ja", ""), old, new)
            q["explanation_ja"] = swap_labels(q.get("explanation_ja", ""), old, new)
            print(f"  p{no:02d}-{i}: 正解 {old} → {new}(選択肢{old}と{new}を入れ替え)")
            touched = True
        if touched:
            json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            changed += 1

    # 組み替え後の姿を確認
    keys, dist = [], collections.Counter()
    for no in range(1, 11):
        d = json.load(open(os.path.join(HERE, "passages", f"p{no:02d}.json"), encoding="utf-8"))
        k = [q["answer"] for q in d["questions"]]
        keys.append(k)
        dist.update(k)
        perm = "★並べ替えのまま" if sorted(k[:4]) == [1, 2, 3, 4] else ""
        print(f"p{no:02d}: {k}  {perm}")
    print(f"\n全体の分布 {dict(sorted(dist.items()))}  / 変更したファイル {changed}")
    print("KEYS = [")
    for k in keys:
        print(f"    {k},")
    print("]")


if __name__ == "__main__":
    sys.exit(main())
