# -*- coding: utf-8 -*-
"""
盲検証用のデータを作る（正解・解説を伏せた「問題だけ」の JSON）。

  python3 _make_blind.py rika_kagaku/content_no01.py  out/blind_kagaku.json
  python3 _make_blind.py natsu_tokkun/content.py      out/blind_tokkun.json  --days

盲ソルバー（別々のエージェント3人）はこの JSON だけを見て解き、
`{"id": "...", "answer": "..."}` の配列を書き出す。それを _reconcile.py が鍵と厳密照合する。

★★ 番号の起点をデータに書き込むこと（過去にこれで四択が全問ズレて「鍵誤り」に見えた）
   本ファイルは **1 始まり**で答えさせる（生徒が①②③④で答えるのに合わせる）。
   content 側の ans は 0 始まり index なので、_reconcile.py が -1 して比べる。
   各設問に answer_format を出すので、ソルバーはそれに従うだけでよい。

★ 記述(desc)は文字列一致で照合できないので **盲検証の対象にしない**
  （代わりに敵対レビューと採点キー整合ゲートで見る）。
"""
import argparse
import importlib.util
import json
import os
import re
import sys

TAG = re.compile(r"<[^>]+>")
# ★組分数・根号の目印は、盲ソルバーには「読める形」で渡す。
#   生の [[frac:3|8]] を見せると、それが何かを説明していないので解答形式が割れる。
_MK_SQRT = re.compile(r"\[\[sqrt:([^\]]+)\]\]")
_MK_FRAC = re.compile(r"\[\[frac:([^|\]]+)\|([^\]]+)\]\]")


def unmark(s):
    s = _MK_SQRT.sub(r"√(\1)", str(s))
    return _MK_FRAC.sub(r"(\1)/(\2)", s)
FMT = {
    "mc": "選択肢の番号を 1 から始まる整数で答える（★0 始まりではない）",
    "calc": "数値と単位をつけて答える（例: 12.5cm）",
    "short": "用語だけを答える（説明文にしない）",
    "order": "並べかえた英文を1文で答える（文頭は大文字、文末はピリオド）",
    "match": "各欄に入る記号を、欄の順にカンマ区切りで答える（例: ア,ウ,エ）",
}


def load(path):
    path = os.path.abspath(path)
    d = os.path.dirname(path)
    sys.path.insert(0, d)
    sys.path.insert(0, os.path.dirname(d))
    spec = importlib.util.spec_from_file_location("_content_" + os.path.basename(d), path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _fmt_for(t, q):
    """★answer_format は設問の中身に合わせて出す。type だけで決めると、
    「最も簡単な整数比で答えよ」に『数値と単位をつけて（例: 12.5cm）』と指示してしまい、
    ソルバーが形式で迷う（実際に盲検証で5人が同じ指摘を出した）。
    冊子には印刷されない指示なので冊子の欠陥ではないが、照合の雑音になる。"""
    body = str(q.get("q", ""))
    if re.search(r"[（(]\s*[アイウエ①-⑨1-9]\s*[）)][^。]{0,40}[（(]\s*[アイウエ①-⑨1-9]\s*[）)]", body):
        return "空欄の順に、カンマ区切りで答える（例: my,mine）"
    if "化学反応式" in body or "化学式" in body:
        return "化学反応式（化学式）で答える。矢印は → を使い、係数と原子の数を正しく書く"
    if t == "calc":
        if re.search(r"整数比|比で答え|最も簡単な比", body):
            # ★例に 3:2 と書いていたら、それがそのまま正答（Mg:O＝3:2）で、
            #   盲ソルバーに答えを教えていた。形式の例は必ず「ありえない値」にする。
            return "最も簡単な整数比を『7:5』のような形で答える（単位は付けない）"
        if re.search(r"何時|何日|時刻|日時", body):
            return "『8月10日午前3時』の形で、日付と時刻を答える"
        if q.get("unit"):
            return f'数値に単位「{q["unit"]}」をつけて答える（例: 12.5{q["unit"]}）'
        return "設問が指示する形で答える（単位があれば付ける）"
    return FMT.get(t, FMT["short"])


def _item(qid, q, ctx=""):
    t = q["type"] if isinstance(q, dict) and "type" in q else "short"
    if t == "desc":
        return None
    it = {"id": qid, "type": t, "question": unmark(q["q"]), "answer_format": _fmt_for(t, q)}
    if ctx:
        it["context"] = TAG.sub(" ", ctx).strip()
    if t == "mc":
        it["choices"] = [f"{i+1}. {unmark(c)}" for i, c in enumerate(q["choices"])]
    if t == "order":
        it["tokens"] = q["tokens"]
    if t == "calc" and q.get("unit"):
        it["unit"] = q["unit"]
    if t == "match":
        it["pool"] = q["pool"]
        it["slots"] = q["slots"]
    return it


def from_parts(C):
    out = []
    n = 1
    for g in C.PART1:
        for it in g["items"]:
            out.append({"id": f"P1-{n}", "type": "short", "question": unmark(it["q"]),
                        "answer_format": FMT["short"]})
            n += 1
    for b in C.PART2:
        ctx = b.get("intro", "") + " " + " ".join(str(f) for f in b.get("figs", []))
        for i, q in enumerate(b["qs"], start=1):
            x = _item(f'{b["no"]}-{i}', q, ctx)
            if x:
                out.append(x)
    return out


def from_days(C):
    out = []
    for D in C.DAYS:
        for sec in D["sections"]:
            for i, q in enumerate(sec["qs"], start=1):
                x = _item(f'D{D["day"]}-{sec["subj"]}-{i}', q)
                if x:
                    x["note"] = f'この設問は「{D["range"]}」の範囲で出題されている'
                    out.append(x)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("content")
    ap.add_argument("out")
    ap.add_argument("--days", action="store_true")
    a = ap.parse_args()
    C = load(a.content)
    items = from_days(C) if a.days else from_parts(C)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump({
            "instruction": "各設問を解いて、[{\"id\": …, \"answer\": …}] の配列で答える。"
                           "answer_format に必ず従うこと。分からなければ推測でよいが、"
                           "空文字にはしない。answer に半角のダブルクォートを入れないこと"
                           "（JSONが壊れる。必要なら「」を使う）。",
            "count": len(items),
            "items": items,
        }, f, ensure_ascii=False, indent=1)
    print(f"WROTE {a.out}  ({len(items)} items)")


if __name__ == "__main__":
    main()
