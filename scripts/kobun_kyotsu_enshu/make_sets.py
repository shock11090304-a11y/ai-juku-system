# -*- coding: utf-8 -*-
"""src/setN.py（執筆順のまま書いた原稿）-> sets/setN.json（刷る形）

   ここでやることは2つだけ。
   1. 正解の位置を、回ごとにあらかじめ決めた番号（pos）へ動かす。
      手で番号を振ると必ず偏る。並べ替えは stem の md5 で決めるので毎回同じ結果になる。
   2. 解説の中の選択肢参照を、並べ替え後の丸数字へ書き直す。
      ★解説には ①②③ を直接書かず、必ず [[0]]〜[[4]]（執筆順の添字）で書くこと。
        直接書くと、並べ替えたときに解説と選択肢がずれる（この事故はこのリポジトリで何度も起きている）。
"""
import os, re, sys, json, glob, hashlib, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "src"))
import positions
SRC = os.path.join(HERE, "src")
DEST = os.path.join(HERE, "sets")
CIRC = "①②③④⑤"

def permute(n_choices, answer, pos, seed_text):
    """執筆順 -> 刷る順 の写像 order を返す。order[新] = 旧添字。
       正解は必ず pos-1 に来る。残りは seed で決まる順（毎回同じ）に並べる。"""
    if not (0 <= answer < n_choices and 1 <= pos <= n_choices):
        raise SystemExit(f"permute: 選択肢{n_choices}個に対して answer={answer} pos={pos} は範囲外")
    others = [i for i in range(n_choices) if i != answer]
    h = hashlib.md5(seed_text.encode("utf-8")).hexdigest()
    others.sort(key=lambda i: hashlib.md5((h + str(i)).encode()).hexdigest())
    order, it = [], iter(others)
    for slot in range(n_choices):
        order.append(answer if slot == pos - 1 else next(it))
    return order

def render_exp(exp, maps, where=""):
    """解説の [[接頭辞+旧添字]] を、並べ替え後の丸数字へ書き直す。
       maps = {小問の接頭辞: {旧添字: 新添字}}。小問が1つの設問は接頭辞が空文字。"""
    def sub(m):
        key, k = m.group(1) or "", int(m.group(2))
        if key not in maps: raise SystemExit(f"{where}解説の参照 [[{key}{k}]] に対応する小問がない")
        if k not in maps[key]: raise SystemExit(f"{where}[[{key}{k}]] が選択肢の範囲外")
        return CIRC[maps[key][k]]
    out = re.sub(r"\[\[([^\d\]]*)(\d)\]\]", sub, exp)
    if "[[" in out: raise SystemExit(f"{where}解説に未解決の参照が残っている")
    return out

def build_set_multi(S):
    """小問が1つの設問は [[0]]〜[[4]]、問1のように小問が複数ある設問は
       小問ごとに [[ア0]] のように接頭辞を付けて参照する（解説が1欄にまとまるため）。"""
    k = 0
    for q in S["questions"]:
        maps = {}
        for it in q["items"]:
            pos = positions.of(S["id"], k); k += 1
            seed = f'{S["id"]}/{q["no"]}/{it.get("label","")}/{it["choices"][0]}'
            order = permute(len(it["choices"]), it["answer"], pos, seed)
            it["choices"] = [it["choices"][i] for i in order]
            it["answer"] = pos - 1
            key = re.sub(r"[()（）]", "", it.get("label", "")) or ""
            if key in maps:
                raise SystemExit(f'第{S["id"]}回 問{q["no"]}: 同じ接頭辞「{key}」の小問が2つある'
                                 "（解説の参照がどちらの並びで解決されるか決まらない）")
            maps[key] = {old: new for new, old in enumerate(order)}
        if re.search(r"[①-⑤]", q["exp"]):
            raise SystemExit(f'第{S["id"]}回 問{q["no"]}: 解説に丸数字が直接書かれている'
                             "（並べ替えでずれる。[[ア0]] の形で書くこと）")
        q["exp"] = render_exp(q["exp"], maps, f'第{S["id"]}回 問{q["no"]}: ')
    return S

def load(path):
    spec = importlib.util.spec_from_file_location(os.path.basename(path)[:-3], path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m.SET

def selftest():
    if not __debug__:
        raise SystemExit("python3 -O では assert が消えるので、この自己テストは意味をなさない")
    """並べ替えと解説の書き直しが本当に対応しているかを、ここで毎回確かめる。
       （検査そのものが壊れていないことを、使う前に確認する）"""
    for ans in range(5):
        for pos in range(1, 6):
            o = permute(5, ans, pos, f"seed{ans}{pos}")
            assert sorted(o) == list(range(5)), o
            assert o[pos - 1] == ans, (ans, pos, o)
            m = {"": {old: new for new, old in enumerate(o)}}
            assert render_exp("[[0]][[1]][[2]][[3]][[4]]", m) == \
                   "".join(CIRC[o.index(k)] for k in range(5))
            assert render_exp("[[ア0]]", {"ア": {0: 3}}) == CIRC[3]
    # 同じ入力なら毎回同じ並びになること
    assert permute(5, 2, 4, "x") == permute(5, 2, 4, "x")
    # 種が違えば並びも変わること（全部同じなら並べ替えが効いていない）
    assert len({tuple(permute(5, 0, 1, f"s{i}")) for i in range(30)}) > 1
    print("selftest: ok")

def main():
    selftest()
    os.makedirs(DEST, exist_ok=True)
    files = sorted(glob.glob(os.path.join(SRC, "set*.py")))
    if not files: raise SystemExit("src/set*.py が無い")
    for f in files:
        S = build_set_multi(load(f))
        out = os.path.join(DEST, os.path.basename(f)[:-3] + ".json")
        json.dump(S, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        ans = [CIRC[it["answer"]] for q in S["questions"] for it in q["items"]]
        print(f'{os.path.basename(out)}: 第{S["id"]}回 正解 {"".join(ans)}')

if __name__ == "__main__":
    main()
