#!/usr/bin/env python3
"""📖 seed-data/eiken_reading_pool_v1.json (英検 長文ドリル: 本文 + 設問) の形式ゲート (run_all_gates.py が拾う)。

固定する不変条件 (壊れると単元ドリルで生徒が誤採点される / 取込で本文ごと skip される):
  - subject は 'eiken'、unit は 4 種 (2級 長文空所補充 / 2級 長文 内容一致 / 準1級 長文空所補充 / 準1級 長文 内容一致)、level は 'standard'
  - 本文は 80 語以上・重複なし・メールアドレス (ASCII の @) を含まない (公開リポジトリ)
  - 空所補充: 本文の空所は「( 1 )( 2 )…」が設問数ぶん順番に 1 回ずつ、設問 k の stem は「( k )」で始まる
  - 設問は本文ごとに 2〜6 問、choices は 4 つ相異、answer は 0〜3、解説は「正解 ①〜④ 正解の文」で始まる
  - 正解位置は単元ごとに散らす (どの位置も 40% 以下)
"""
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED = os.path.join(REPO, "seed-data", "eiken_reading_pool_v1.json")
UNITS = ["2級 長文空所補充", "2級 長文 内容一致", "準1級 長文空所補充", "準1級 長文 内容一致"]
CIRCLED = "①②③④"
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def main():
    d = json.load(open(SEED, encoding="utf-8"))
    ps = d.get("passages") or []
    bad = []
    seen = {}
    pos = {u: [0, 0, 0, 0] for u in UNITS}
    nq = 0
    if d.get("subject") != "eiken":
        bad.append(f"subject={d.get('subject')!r}")
    for p in ps:
        src = p.get("source", "?")
        unit = p.get("unit")
        if unit not in UNITS:
            bad.append(f"{src}: unit={unit!r}")
        if p.get("level") != "standard":
            bad.append(f"{src}: level={p.get('level')!r}")
        body = p.get("body") or ""
        if len(re.findall(r"[A-Za-z]+", body)) < 80:
            bad.append(f"{src}: 本文が短い")
        k = re.sub(r"\s+", " ", body).strip().lower()
        if k in seen:
            bad.append(f"{src}: 本文が {seen[k]} と重複")
        seen[k] = src
        if EMAIL_RE.search(body + (p.get("body_ja") or "")):
            bad.append(f"{src}: 本文にメールアドレス")
        qs = p.get("questions") or []
        if not (2 <= len(qs) <= 6):
            bad.append(f"{src}: 設問 {len(qs)} 問")
        if unit and "空所" in unit:
            marks = re.findall(r"\(\s*(\d{1,2})\s*\)", body)
            if marks != [str(i) for i in range(1, len(qs) + 1)]:
                bad.append(f"{src}: 空所の並び {marks}")
        for i, q in enumerate(qs, 1):
            nq += 1
            stem = q.get("stem") or ""
            ch = q.get("choices") or []
            a = q.get("answer")
            ex = q.get("explanation") or ""
            if not stem:
                bad.append(f"{src} 問{i}: stem が空")
            if unit and "空所" in unit and not stem.startswith(f"( {i} )"):
                bad.append(f"{src} 問{i}: stem が ( {i} ) で始まらない")
            if len(ch) != 4 or len(set(x.strip().lower() for x in ch)) != 4 or any(not x.strip() for x in ch):
                bad.append(f"{src} 問{i}: choices={ch}")
            if not isinstance(a, int) or not (0 <= a <= 3):
                bad.append(f"{src} 問{i}: answer={a!r}")
                continue
            if ch and not ex.startswith(f"正解 {CIRCLED[a]} "):
                bad.append(f"{src} 問{i}: 解説が「正解 {CIRCLED[a]} 」で始まらない")
            if len(ex) < 30:
                bad.append(f"{src} 問{i}: 解説が短い")
            if EMAIL_RE.search(stem + " ".join(ch) + ex):
                bad.append(f"{src} 問{i}: メールアドレス")
            if unit in pos:
                pos[unit][a] += 1
    for u, v in pos.items():
        if sum(v) == 0:
            bad.append(f"単元 {u} が 0 問")
        elif max(v) / sum(v) > 0.40:
            bad.append(f"単元 {u} の正解位置が偏っている {v}")
    print(f"eiken_reading_pool_v1: 本文 {len(ps)} 本 / 設問 {nq} 問 / 単元別 {{ {', '.join(f'{u}: {sum(v)}' for u, v in pos.items())} }}")
    if bad:
        print(f"❌ VIOLATION {len(bad)} 件")
        for b in bad[:60]:
            print("  -", b)
        sys.exit(1)
    print("✅ ALL PASS (英検 長文シードの形式)")


if __name__ == "__main__":
    main()
