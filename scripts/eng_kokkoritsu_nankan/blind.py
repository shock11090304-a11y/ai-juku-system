#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""盲検証ハーネス。「LLM は解く／Python が照合する」を守るための2コマンド。

  python3 blind.py make <出力ディレクトリ>     # 正解を伏せた問題ファイルを書く
  python3 blind.py reconcile <出力ディレクトリ> # 3人の解答 A/B/C と鍵を厳密照合

★LLM に一致判定をさせない。非決定でミスが漏れる（既知の失敗）。
★和文英訳は「唯一解」が存在しないので照合対象外（採点要素の妥当性は別レビューで見る）。
"""
import json
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
# ★機械（ゲート・組版・盲検証）は共有し、中身だけ差し替える。
#   WORKBOOK_DIR=<別冊のディレクトリ> を付けて実行すると、そちらの content.py を読む。
BOOK_DIR = os.path.abspath(os.environ.get("WORKBOOK_DIR") or HERE)
sys.path.insert(0, BOOK_DIR)
sys.path.insert(0, os.path.dirname(HERE))

from content import BOOK  # noqa: E402

GRADED = ("mc", "error", "order", "fill", "ident", "rewrite")


def qid(p, s, i):
    return f'P{p["no"]}-Q{s["no"]}-{i:02d}'


def iter_q():
    for p in BOOK["parts"]:
        for s in p["sections"]:
            for i, it in enumerate(s["items"], 1):
                yield p, s, i, it


def norm(s):
    """短縮形・冠詞の揺れを吸収しない厳密正規化（小文字・句読点除去・空白畳み）。"""
    s = re.sub(r"[.,;:!?\"'“”‘’]", " ", str(s).lower())
    return re.sub(r"\s+", " ", s).strip()


# --------------------------------------------------------------------- make
def make(outdir):
    os.makedirs(outdir, exist_ok=True)
    qs, key = [], {}
    for p, s, i, it in iter_q():
        k = qid(p, s, i)
        q = {"id": k, "kind": s["kind"], "level": p["level"], "instruction": s["inst"]}
        if s["kind"] == "mc":
            q["sentence"], q["choices"] = it["stem"], it["choices"]
            # ★鍵は1始まり（生徒が①②③④で答えるのに合わせる）。data 側の ans は0始まり。
            #   この番号の起点をソルバーに伝え忘れると、全問ずれて「鍵誤り」に見える
            #   （実際に一度やった。0始まり/1始まりの取り違えはこのリポジトリで再発中）。
            q["answer_format"] = "選択肢の番号を 1〜4 の整数で答える（1＝最初の選択肢）"
            key[k] = {"kind": "mc", "ans": str(it["ans"] + 1)}
        elif s["kind"] == "error":
            q["sentence"] = it["stem"]
            q["underlined"] = {c: it["parts"][j] for j, c in enumerate("abcd")}
            key[k] = {"kind": "error", "ans": "abcd"[it["ans"]], "fix": it["fix"]}
        elif s["kind"] == "order":
            q["japanese"], q["frame"] = it["ja"], it["frame"]
            q["tokens"] = sorted(it["tokens"], key=str.lower)
            key[k] = {"kind": "order", "ans": it["ans"]}
        elif s["kind"] in ("fill", "ident"):
            q["sentence"] = it["stem"]
            if it.get("given"):
                q["given_word"] = it["given"]
            if it.get("hint"):
                q["first_letter"] = it["hint"]
            key[k] = {"kind": "fill", "ans": it["ans"], "accept": it.get("accept", [])}
        elif s["kind"] == "rewrite":
            q["original"], q["direction"] = it["src"], it["inst"]
            key[k] = {"kind": "rewrite", "ans": it["ans"], "accept": it.get("accept", [])}
        elif s["kind"] == "jtrans":
            q["context"], q["underlined"] = it["context"], it["src"]
            key[k] = {"kind": "jtrans", "ans": it["model"]}
        else:
            q["japanese"] = it["ja"]
            key[k] = {"kind": "trans", "ans": it["model"]}
        qs.append(q)

    blind = [q for q in qs if q["kind"] in GRADED]
    with open(os.path.join(outdir, "blind.json"), "w") as f:
        json.dump(blind, f, ensure_ascii=False, indent=1)
    with open(os.path.join(outdir, "_key.json"), "w") as f:
        json.dump(key, f, ensure_ascii=False, indent=1)
    print(f"blind.json: 採点対象 {len(blind)}問"
          f"（和訳・英訳{len(qs)-len(blind)}問は唯一解が無いため照合対象外）")
    print(f"→ {outdir}")


# ---------------------------------------------------------------- reconcile
def reconcile(outdir):
    key = json.load(open(os.path.join(outdir, "_key.json")))
    solvers = {}
    for name in "ABC":
        path = os.path.join(outdir, f"answers_{name}.json")
        if os.path.exists(path):
            solvers[name] = {d["id"]: d.get("answer", "") for d in json.load(open(path))}
    if not solvers:
        sys.exit("answers_A/B/C.json が無い")
    print(f"■ ソルバー {', '.join(solvers)} × 鍵 {len(key)}問\n")

    mismatch, key_error, disagree = [], [], []
    for k, kv in key.items():
        if kv["kind"] in ("trans", "jtrans"):
            continue
        if kv["kind"] == "error":
            gold = {norm(kv["ans"])}
        else:
            gold = {norm(kv["ans"])} | {norm(a) for a in kv.get("accept", [])}
        got = {n: norm(solvers[n].get(k, "")) for n in solvers}
        wrong = [n for n, v in got.items() if v not in gold]
        if not wrong:
            continue
        line = f'{k}  鍵「{kv["ans"]}」' + "".join(
            f'／{n}「{solvers[n].get(k,"")}」' for n in wrong)
        if len(wrong) == len(solvers):
            # 全員が鍵と違う＝本物の鍵誤りの最強シグナル
            (key_error if len(set(got.values())) == 1 else disagree).append(line)
        else:
            mismatch.append(line)

    graded = sum(1 for v in key.values() if v["kind"] not in ("trans", "jtrans"))
    print(f"● 全員一致で鍵と同じ : {graded - len(key_error) - len(disagree) - len(mismatch)}問")
    for title, rows in (("★鍵誤りの疑い（全員が同じ別解答）", key_error),
                        ("★出題不成立の疑い（全員が鍵と違い、かつ三者バラバラ）", disagree),
                        ("要確認（一部のソルバーだけ不一致＝別解の可能性）", mismatch)):
        print(f"\n● {title}: {len(rows)}件")
        for r in rows:
            print("   ", r)
    return not (key_error or disagree)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    (make if sys.argv[1] == "make" else reconcile)(sys.argv[2])
