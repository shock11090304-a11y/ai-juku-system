# -*- coding: utf-8 -*-
"""data/L*.json の受け入れ検査と、四択の正解位置の均し。

使い方:
  python3 scripts/kobun_bunpo_12/ingest.py            # 検査だけ
  python3 scripts/kobun_bunpo_12/ingest.py --balance  # 正解位置を均して書き戻す

check.py（機械ゲート）の前段。並列に書かせた JSON が構造として揃っているかを見る。
★check.py は「冊子として成立しているか」を見るが、ここは「JSON が仕様どおりか」を見る。
  層を分けているのは、構造が崩れていると check.py が意味不明な場所で落ちて原因が読めないため。
"""
import glob
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

# 1講の形（大問番号 → (kind, 問数, 1問の配点)）
SHAPE = {1: ("mc", 5, 4), 2: ("fill", 4, 3), 3: ("ident", 3, 4), 4: ("jtrans", 1, 6)}
BLANK = "(        )"

# ★この順で刷るのが普通の選択肢群。順番に意味があるので並べ替えない
CANON = [
    ["未然形", "連用形", "終止形", "連体形", "已然形", "命令形"],
    ["四段活用", "上一段活用", "下一段活用", "上二段活用", "下二段活用",
     "カ行変格活用", "サ行変格活用", "ナ行変格活用", "ラ行変格活用"],
    ["四段", "上一段", "下一段", "上二段", "下二段", "カ変", "サ変", "ナ変", "ラ変"],
    ["尊敬語", "謙譲語", "丁寧語"],
]


def is_canon(choices):
    """選択肢が、決まった順序を持つ一覧の部分列になっているか。"""
    for canon in CANON:
        idx = [canon.index(c) for c in choices if c in canon]
        if len(idx) == len(choices) and idx == sorted(idx):
            return True
    return False


def check(parts):
    bad = []

    def err(where, msg):
        bad.append(f"{where}: {msg}")

    for p in parts:
        w0 = f'第{p["no"]}部'
        for k in ("no", "level", "ref", "aim", "time", "steps", "sections"):
            if not p.get(k):
                err(w0, f"{k} が無い")
        if len(p.get("steps", [])) != 3:
            err(w0, f'steps が3手順でない（{len(p.get("steps", []))}）')
        secs = p.get("sections", [])
        if len(secs) != 4:
            err(w0, f"大問が4つでない（{len(secs)}）")
        for s in secs:
            want = SHAPE.get(s.get("no"))
            w = f'{w0} 大問{s.get("no")}'
            if not want:
                err(w, "大問番号が 1〜4 でない")
                continue
            kind, n, pt = want
            if s.get("kind") != kind:
                err(w, f'kind が {kind} でない（{s.get("kind")}）')
            if len(s.get("items", [])) != n:
                err(w, f'問数が {n} でない（{len(s.get("items", []))}）')
            if s.get("pt") != pt:
                err(w, f'配点が {pt} でない（{s.get("pt")}）')
            if not s.get("inst") or not s.get("title"):
                err(w, "title / inst が無い")

            for i, it in enumerate(s.get("items", []), 1):
                wi = f"{w}-{i}"
                exp = str(it.get("exp", ""))
                if len(exp) < 40:
                    err(wi, f"exp が40字未満（{len(exp)}字）")
                if not it.get("point"):
                    err(wi, "point が無い")
                stem = str(it.get("stem", ""))
                if stem.count("＿") % 2:
                    err(wi, "傍線 ＿ の数が奇数（対になっていない）")

                if kind == "mc":
                    ch = it.get("choices") or []
                    if len(ch) != 4:
                        err(wi, f"選択肢が4つでない（{len(ch)}）")
                    a = it.get("ans")
                    if not isinstance(a, int) or not 0 <= a < len(ch):
                        err(wi, f"ans が 0〜3 の整数でない（{a!r}）★0始まり index")
                    if len(set(ch)) != len(ch):
                        err(wi, "選択肢が重複している")
                elif kind == "fill":
                    if BLANK not in stem:
                        err(wi, "空所 (半角スペース8個) が stem に無い")
                    if not it.get("ans"):
                        err(wi, "ans が無い")
                elif kind == "ident":
                    if "＿" not in stem:
                        err(wi, "傍線 ＿ が無い")
                    if not it.get("ans"):
                        err(wi, "ans が無い")
                elif kind == "jtrans":
                    els = it.get("elements") or []
                    if len(els) != 3 or sum(e[1] for e in els) != pt:
                        err(wi, f"elements が3個×2点=6点でない（{els}）")
                    for f in ("context", "src", "model", "alts"):
                        if not it.get(f):
                            err(wi, f"{f} が無い")
    return bad


def balance(parts):
    """四択の正解位置を stem の md5 順で散らす（決まった順序を持つ選択肢群は除く）。
    ★手で番号を振ると必ず偏る（英文法の初版は34問中19問が2番に集中した）。
    解説は選択肢の番号を参照していないので、並べ替えても安全。"""
    mcs = [it for p in parts for s in p["sections"]
           if s["kind"] == "mc" for it in s["items"]]
    free = [it for it in mcs if not is_canon(it["choices"])]
    order = sorted(range(len(free)),
                   key=lambda i: hashlib.md5(free[i]["stem"].encode()).hexdigest())
    for rank, i in enumerate(order):
        it = free[i]
        ch, a, target = it["choices"], it["ans"], rank % 4
        rest = ch[:a] + ch[a + 1:]
        it["choices"] = rest[:target] + [ch[a]] + rest[target:]
        it["ans"] = target
    return len(free), len(mcs) - len(free)


def main():
    files = sorted(glob.glob(os.path.join(DATA, "L*.json")))
    if not files:
        raise SystemExit(f"データが無い: {DATA}/L*.json")
    parts, per_file = [], {}
    for path in files:
        with open(path, encoding="utf-8") as f:
            p = json.load(f)
        per_file[path] = p
        parts.append(p)

    print(f"■ {len(files)}講 / {sum(len(s['items']) for p in parts for s in p['sections'])}問\n")
    bad = check(parts)
    if bad:
        print(f"✗ 受け入れ検査 NG {len(bad)}件")
        for b in bad:
            print("   ", b)
        return 1
    print("✓ 受け入れ検査 OK（構造・配点・ans範囲・exp字数・傍線対応）")

    if "--balance" in sys.argv:
        moved, kept = balance(parts)
        for path, p in per_file.items():
            with open(path, "w", encoding="utf-8") as f:
                json.dump(p, f, ensure_ascii=False, indent=1)
        print(f"✓ 正解位置を均した: 並べ替え{moved}問 ／ 順序を保った{kept}問")

    # 正解位置の分布を必ず出す（偏っていたら人が気づけるように）
    dist = [0, 0, 0, 0]
    for p in parts:
        for s in p["sections"]:
            if s["kind"] == "mc":
                for it in s["items"]:
                    dist[it["ans"]] += 1
    print(f"  四択の正解位置 ①{dist[0]} ②{dist[1]} ③{dist[2]} ④{dist[3]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
