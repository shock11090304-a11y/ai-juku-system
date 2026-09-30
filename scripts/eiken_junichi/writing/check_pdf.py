# -*- coding: utf-8 -*-
"""英検準1級 ライティング対策プリント — 刷り上がり PDF と正典データの突き合わせ (相互チェック ①)

    python3 scripts/eiken_junichi/writing/build.py      # 先に刷る
    python3 scripts/eiken_junichi/writing/check_pdf.py

PDF は生成物なのでリポジトリに無い (CI は run_all_gates.py --no-pdf でこのゲートを外す)。
PDF が無ければ落ちる = 「build を回し忘れている」の合図。

見ること:
  ② 問題      Set k の要約は 1+2(k-1) ページ目に本文 3 段落が全部、意見論述は次のページに TOPIC と POINTS が全部
  ③ 解答解説  Set k の要約の解答例・言い換え・削った情報が 1 ページに、意見論述の解答例 4 段落・表現・反対の骨子が次の 1 ページに
             (= 1 題 1 ページからあふれていない)
  ① コツ      例題の本文・解答例がすべて刷られ、意見論述の例題が 1 ページに収まっている
"""
import json
import os
import re
import sys
import unicodedata

import fitz  # noqa: E402  (run_all_gates.py --no-pdf はトップレベルの fitz を見て外す)

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build  # noqa: E402  (BOOKS / OUT / load を共有する)

errors = []


def norm(t):
    """空白をすべて落として比べる。日本語は行末で折り返すと抽出時に空白が入るため
    (「足り␣なくなる」)、空白の有無で照合すると必ず外れる。語の欠けは空白を落としても検出できる。"""
    t = unicodedata.normalize("NFKC", t)
    return re.sub(r"\s+", "", t)


def pages(key):
    path = os.path.join(build.OUT, build.BOOKS[key])
    if not os.path.exists(path):
        print(f"NG: PDF が無い {path} (先に build.py を回す)")
        print("=== FAIL 1 ===")
        sys.exit(1)
    d = fitz.open(path)
    return [norm(p.get_text()) for p in d]


def need(where, page_text, frags):
    for f in frags:
        if norm(f) not in page_text:
            errors.append(f"{where}: 刷り上がりに無い「{f[:60]}…」")


def main():
    ex, sets = build.load()
    n = len(sets)
    g, m, k = pages("guide"), pages("mondai"), pages("kaitou")
    print(f"[check] ① {len(g)} ページ / ② {len(m)} ページ / ③ {len(k)} ページ ・ 演習 {n} セット")
    if len(m) != 1 + 2 * n:
        errors.append(f"② 問題のページ数 {len(m)} (1 + 2×{n} のはず。あふれか欠け)")
    if len(k) != 1 + 2 * n:
        errors.append(f"③ 解答解説のページ数 {len(k)} (1 + 2×{n} のはず。1 題 1 ページからあふれている)")
    for i, d in enumerate(sets):
        s, e = d["summary"], d["essay"]
        ps, pe = 1 + 2 * i, 2 + 2 * i
        tag = f"Set {d['no']}"
        if ps < len(m):
            need(f"② {tag} 要約 p{ps + 1}", m[ps], s["paras"] + [tag, "語数"])
        if pe < len(m):
            need(f"② {tag} 意見 p{pe + 1}", m[pe], [e["topic"], tag, "語数"] + e["points"])
        if ps < len(k):
            need(f"③ {tag} 要約 p{ps + 1}", k[ps], [s["model"], tag] +
                 [p["src"] for p in s["paraphrases"]] + [p["dst"] for p in s["paraphrases"]] +
                 [o["src"] for o in s["omitted"]] + [s["note_ja"]])
        if pe < len(k):
            need(f"③ {tag} 意見 p{pe + 1}", k[pe], e["paras"] + [e["topic"], e["note_ja"], e["opposite"]["stance_en"]] +
                 [x["en"] for x in e["expressions"]] + [r["topic_en"] for r in e["opposite"]["reasons"]])
    # あふれ検出: 柱とノンブルだけの (本文がほぼ空の) ページがあれば、前のページからのはみ出し
    for name, book in (("①", g), ("②", m), ("③", k)):
        for i, t in enumerate(book, 1):
            body = re.sub(r"\d+/\d+|英検準1級ライティング対策[①②③1-3][^|｜]*[|｜]トリリオンAI塾", "", t)
            if len(body) < 40:
                errors.append(f"{name} p{i}: 本文がほぼ空のページ (前のページからのあふれ)")
    whole = " ".join(g)
    need("① 要約の例題", whole, ex["summary"]["paras"] + [ex["summary"]["model"]])
    eg = [t for t in g if norm(ex["essay"]["topic"]) in t and norm(ex["essay"]["paras"][0]) in t]
    if not eg:
        errors.append("① 意見論述の例題: TOPIC と解答例が同じページに無い")
    else:
        need("① 意見論述の例題 (1 ページ)", eg[0], ex["essay"]["paras"] + [ex["essay"]["opposite"]["stance_en"]] +
             [r["topic_en"] for r in ex["essay"]["opposite"]["reasons"]])
    for no in range(1, 9):
        if not any(re.search(rf"{no}(?:ライティングの全体像|要約の|意見論述の|よくあるミス|使える表現集|問題演習の進め方|試験までの|セルフチェック)", t) for t in g):
            errors.append(f"① 見出し {no} が見つからない")
    if errors:
        for x in errors:
            print("NG:", x)
        print(f"=== FAIL {len(errors)} ===")
        sys.exit(1)
    print("=== ALL PASS (0 warnings) ===")


if __name__ == "__main__":
    main()
