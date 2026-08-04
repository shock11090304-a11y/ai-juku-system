#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""化学プリントの機械検証(盲解答で測れない軸を Python で潰す)。

  python3 verify_chem.py

検証する軸:
  A 数値再計算   verify_py を実行し result == verify_expected か
  B 答との一致   verify_expected が answer の文中の数値と一致するか(有効数字の取り違え検出)
  C 新課程準拠   熱化学方程式(= ... + Q kJ)の残骸・旧用語のみの記述がないか
  D KaTeX 健全性 $ の対応・裸の化学式(H2SO4 等が $ の外に落ちている)
  E 解説の型     ▶ ① ② ③ ★ が揃っているか・途中式に数値があるか
  F 解答漏洩     stem に answer の数値がそのまま書かれていないか
  G 構成         18単元×6問・レベル配分・skill の付与
"""
import os, re, sys, json, math, io, contextlib

HERE = os.path.dirname(os.path.abspath(__file__))
PRIV = os.path.join(HERE, "parts_private")

NG = []          # 落ちたら直すべきもの
WARN = []        # 目視確認したいもと


def add(bucket, pid, axis, msg):
    bucket.append(f"[{axis}] {pid}  {msg}")


# ---------------------------------------------------------------- 数値抽出
NUM_RE = re.compile(r"""
    (?P<mant>[-+]?\d+(?:\.\d+)?)          # 仮数
    (?:\s*\\times\s*10\^\{?(?P<exp>[-+]?\d+)\}?)?   # \times10^{-3}
""", re.X)


def numbers_in(s):
    """文字列中の数値を(指数表記込みで)すべて拾う。"""
    out = []
    for m in NUM_RE.finditer(s or ""):
        v = float(m.group("mant"))
        if m.group("exp"):
            v *= 10.0 ** int(m.group("exp"))
        out.append(v)
    return out


def close(a, b, tol):
    if a == 0 or b == 0:
        return abs(a - b) <= (tol or 0.02)
    return abs(a - b) / abs(b) <= (tol or 0.02)


# ---------------------------------------------------------------- 各軸
def check_verify_py(pid, q):
    code, exp = q.get("verify_py"), q.get("verify_expected")
    if not code:
        return False
    if exp is None:
        add(NG, pid, "A", "verify_py があるのに verify_expected が null")
        return False
    env = {"math": math, "__builtins__": __builtins__}
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            exec(code, env)
    except Exception as e:                                     # noqa: BLE001
        add(NG, pid, "A", f"verify_py が実行時エラー: {type(e).__name__}: {e}")
        return False
    if "result" not in env:
        add(NG, pid, "A", "verify_py が result を定義していない")
        return False
    got = env["result"]
    if isinstance(got, bool) or not isinstance(got, (int, float)):
        add(NG, pid, "A", f"result が数値でない: {got!r}")
        return False
    tol = q.get("verify_tol") or 0.02
    if not close(float(got), float(exp), tol):
        add(NG, pid, "A", f"再計算 {got:.6g} ≠ 宣言値 {exp:.6g} (許容{tol})")
        return False
    # B: answer の中に expected と一致する数値があるか
    cands = numbers_in(q.get("answer", ""))
    if cands and not any(close(c, float(exp), max(tol, 0.03)) for c in cands):
        add(NG, pid, "B", f"answer の数値 {cands} に検算値 {exp:.6g} が無い → 答えの写し間違い/有効数字ずれ")
    return True


OLD_THERMO = [
    (re.compile(r"=\s*[^=]{0,40}?[+\-]\s*\d[\d.]*\s*(?:\\,)?\s*(?:\\mathrm\{)?kJ"), "熱化学方程式(= …± Q kJ)の形が残っている"),
]
OLD_WORDS = ["生成熱", "燃焼熱", "中和熱", "溶解熱", "反応熱"]


def check_newcurriculum(pid, q):
    blob = " ".join([q.get("stem", ""), q.get("answer", ""), q.get("explanation", "")])
    for rx, msg in OLD_THERMO:
        if rx.search(blob):
            add(NG, pid, "C", msg)
    used_old = [w for w in OLD_WORDS if w in blob]
    if used_old and "Delta H" not in blob and "ΔH" not in blob:
        add(NG, pid, "C", f"旧課程用語 {used_old} のみで ΔH 表記が無い")


BARE_FORMULA = re.compile(r"(?<![A-Za-z\\{])((?:H2O|H2SO4|HCl|NaOH|CO2|O2|H2|N2|NH3|CH4|CaCO3|NaCl|CuSO4|Cl2|SO2|NO2|HNO3|KOH|AgNO3|ZnSO4|PbSO4|H3PO4|C2H5OH|CaCl2|MgCl2|Fe2O3|Al2O3)|[A-Z][a-z]?\^?\d?\+)")


def check_katex(pid, q):
    for field in ("stem", "answer", "explanation"):
        s = q.get(field, "") or ""
        if s.count("$") % 2 != 0:
            add(NG, pid, "D", f"{field}: $ の数が奇数({s.count('$')})→ KaTeX が壊れる")
        # $...$ の外側だけを取り出して裸の化学式を探す
        outside = "".join(re.split(r"\$[^$]*\$", s))
        m = BARE_FORMULA.search(outside)
        if m and m.group(0) not in ("A", "B", "C", "D", "E", "I", "V", "T", "P", "K", "R", "L"):
            add(WARN, pid, "D", f"{field}: $ の外に裸の化学式らしき '{m.group(0)}'")


def check_explanation(pid, q):
    e = q.get("explanation", "") or ""
    if not e.strip():
        add(NG, pid, "E", "解説が空")
        return
    if "▶" not in e:
        add(NG, pid, "E", "解説に ▶(考え方)が無い")
    if "★" not in e:
        add(NG, pid, "E", "解説に ★(合言葉)が無い")
    steps = sum(1 for c in "①②③④⑤" if c in e)
    if steps < 2:
        add(NG, pid, "E", f"手順の丸数字が {steps} 個しかない")
    if len(e) < 120:
        add(WARN, pid, "E", f"解説が短い({len(e)}字)")


# group 見出しは問題編にも印刷される。判断を問う問題で、見出しに「結論の語」が
# 入っていると答えがそのまま読める。★実例: C14-5 の「圧力で動かない平衡と触媒」が
# (2)の答え「移動しない」を露出していた(答えの文字列とは一致しないので機械照合では出ない)。
VERDICT_WORDS = ["動かない", "変わらない", "移動しない", "残らない", "残る", "できない",
                 "等しい", "同じ", "増える", "減る", "大きくなる", "小さくなる",
                 "近づく", "右へ", "左へ", "全部気体"]


def check_group_verdict(pid, q):
    g = q.get("group", "") or ""
    # 「残るかの判定」のような疑問形は問いの型を言っているだけで、結論ではない
    hit = [w for w in VERDICT_WORDS
           if w in g and not g[g.index(w) + len(w):].startswith(("か", "かどうか"))]
    if not hit:
        return
    # 「どちらか/なぜか/判定せよ」型の設問だけが危ない(計算問題の見出しなら無害)
    stem = q.get("stem", "")
    if any(k in stem for k in ("どちら", "答えよ", "説明せよ", "述べよ", "判定")):
        add(WARN, pid, "F", f"group 見出し「{g}」に結論の語 {hit} が入っている→"
                            f"問題編でこの見出しが答えのヒントになっていないか目視すること")


def check_leak(pid, q):
    """stem に答えの数値が書かれていないか。"""
    exp = q.get("verify_expected")
    if exp is None:
        return
    for v in numbers_in(q.get("stem", "")):
        if close(v, float(exp), 0.001) and abs(float(exp)) > 1e-9:
            add(WARN, pid, "F", f"stem に答えと同じ数値 {v:.6g} が出ている(与件なら可・要目視)")
            break


# ---------------------------------------------------------------- main
def main():
    n_q = n_verified = 0
    unit_no = 0
    skills = {}
    for n in range(1, 7):
        path = os.path.join(PRIV, f"part{n}.json")
        if not os.path.exists(path):
            add(NG, f"part{n}", "G", "ファイルが無い")
            continue
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        if len(d.get("units", [])) != 3:
            add(NG, f"part{n}", "G", f"単元数が {len(d.get('units', []))}(3であるべき)")
        if not (d.get("overview") or "").strip():
            add(NG, f"part{n}", "G", "overview(攻略の手順)が空")
        for u in d["units"]:
            unit_no += 1
            probs = u["problems"]
            if len(probs) != 6:
                add(NG, f"{unit_no:02d}", "G", f"問題数が {len(probs)}(6であるべき)")
            lv = [p.get("level") for p in probs]
            if lv and lv[0] != "basic":
                add(NG, f"{unit_no:02d}", "G", f"1問目が basic でない({lv[0]})")
            if lv.count("basic") < 1 or lv.count("standard") < 1:
                add(WARN, f"{unit_no:02d}", "G", f"レベル配分が偏っている {lv}")
            n_vp = sum(1 for p in probs if p.get("verify_py"))
            if n_vp < 3:
                add(WARN, f"{unit_no:02d}", "G", f"verify_py 付きが {n_vp}問しかない(4問以上が目安)")
            for j, q in enumerate(probs, 1):
                pid = f"{unit_no:02d}-{j}"
                n_q += 1
                if not (q.get("skill") or "").strip():
                    add(NG, pid, "G", "skill が空")
                skills.setdefault(q.get("skill", "?"), []).append(pid)
                if check_verify_py(pid, q):
                    n_verified += 1
                check_newcurriculum(pid, q)
                check_katex(pid, q)
                check_explanation(pid, q)
                check_leak(pid, q)
                check_group_verdict(pid, q)

    print(f"問題数 {n_q}  /  単元 {unit_no}  /  数値再計算に成功 {n_verified}問  /  skill種 {len(skills)}")
    print(f"NG {len(NG)} 件 / WARN {len(WARN)} 件\n")
    for s in NG:
        print("NG   " + s)
    if WARN:
        print()
    for s in WARN:
        print("warn " + s)
    return 1 if NG else 0


if __name__ == "__main__":
    sys.exit(main())
