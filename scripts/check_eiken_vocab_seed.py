#!/usr/bin/env python3
"""🏅 seed-data/eiken_vocab_pool_v1.json の形式ゲート (run_all_gates.py が拾う)。

固定する不変条件 (壊れると単元ドリルで生徒が誤採点される / 取込で黙って skip される):
  - subject は 'eiken'、unit は 4 種 (2級 単語 / 2級 句動詞・熟語 / 準1級 単語 / 準1級 句動詞・熟語)、level は 'standard'
  - stem に空所 "(   )" がちょうど 1 つ
  - choices は 4 つ相異、answer は 0〜3、解説に正解語が出る、解説に ①〜④ や「選択肢2」を書かない
  - stem は一意 (取込の dedup は stem+unit+subject なので、同じ stem を別 unit に入れると二重に出る)
  - 正解位置は単元ごとに散らす (どの位置も 40% 以下)
"""
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED = os.path.join(REPO, "seed-data", "eiken_vocab_pool_v1.json")
UNITS = ["2級 単語", "2級 句動詞・熟語", "準1級 単語", "準1級 句動詞・熟語"]


def main():
    d = json.load(open(SEED, encoding="utf-8"))
    qs = d.get("questions") or []
    bad = []
    seen = {}
    pos = {u: [0, 0, 0, 0] for u in UNITS}
    for q in qs:
        src = q.get("source", "?")
        if q.get("subject") != "eiken":
            bad.append(f"{src}: subject={q.get('subject')!r}")
        if q.get("unit") not in UNITS:
            bad.append(f"{src}: unit={q.get('unit')!r}")
        if q.get("level") != "standard":
            bad.append(f"{src}: level={q.get('level')!r}")
        stem = q.get("stem") or ""
        if stem.count("(   )") != 1:
            bad.append(f"{src}: 空所が {stem.count('(   )')} 個")
        ch = q.get("choices") or []
        if len(ch) != 4 or len(set(x.strip().lower() for x in ch)) != 4 or any(not x.strip() for x in ch):
            bad.append(f"{src}: choices={ch}")
        a = q.get("answer")
        if not isinstance(a, int) or not (0 <= a <= 3):
            bad.append(f"{src}: answer={a!r}")
        ex = q.get("explanation") or ""
        if isinstance(a, int) and 0 <= a <= 3 and ch and ch[a].lower() not in ex.lower():
            bad.append(f"{src}: 解説に正解語 {ch[a]!r} が無い")
        if re.search(r"[①②③④]|選択肢\s*[1-4１-４]|\{\s*[1-4]\s*:|(?<=[ぁ-んァ-ヶ一-龥])[1-4](?=のみ|だけ|が(?:文意|適切|自然|正解)|[。、]|\s|$)", ex):
            bad.append(f"{src}: 解説に番号参照")
        if len(ex) < 20:
            bad.append(f"{src}: 解説が短い ({len(ex)} 字)")
        k = stem.strip().lower()
        if k in seen:
            bad.append(f"{src}: stem が {seen[k]} と重複")
        seen[k] = src
        if q.get("unit") in pos and isinstance(a, int) and 0 <= a <= 3:
            pos[q["unit"]][a] += 1
    for u, v in pos.items():
        if sum(v) == 0:
            bad.append(f"単元 {u} が 0 問")
        elif max(v) / sum(v) > 0.40:
            bad.append(f"単元 {u} の正解位置が偏っている {v}")
    print(f"eiken_vocab_pool_v1: {len(qs)} 問 / 単元別 {{ {', '.join(f'{u}: {sum(v)}' for u, v in pos.items())} }}")
    if bad:
        print(f"❌ VIOLATION {len(bad)} 件")
        for b in bad[:60]:
            print("  -", b)
        sys.exit(1)
    print("✅ ALL PASS (英検 語彙シードの形式)")


if __name__ == "__main__":
    main()
