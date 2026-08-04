# -*- coding: utf-8 -*-
r"""verify_math1a_b.py — math1a_b.py の全マークスロットを独立計算で検証する。

方針: SECTIONS/ANS_SECTIONS の値を「使わずに」ゼロから再計算し、
      ANS_SECTIONS の slots と一致することを assert する。
  第3問: 平面幾何(角の二等分線・方べき)+座標計算(F=PI∩DE, 体積)を sympy で厳密に。
  第4問: 3人・4人リーグ戦を全対戦結果 2^3 / 2^6 通り全数列挙し、抽選込みで A の優勝確率を
         厳密分数で求める。各サブ確率(表2の巴・D全敗・部分ケース)も独立列挙で照合。

実行: python3 content/verify_math1a_b.py  → 全 assert 通過で "ALL VERIFY PASS"
"""
import importlib.util
import os
from math import gcd, isqrt
from fractions import Fraction
from itertools import product

import sympy as sp

HERE = os.path.dirname(os.path.abspath(__file__))


def load():
    spec = importlib.util.spec_from_file_location("m1b", os.path.join(HERE, "math1a_b.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


MOD = load()
ANS = {s["section"]: s["slots"] for s in MOD.ANS_SECTIONS}
CIRC = "⓪①②③④⑤⑥⑦⑧⑨"


def circ(i):
    return CIRC[i]


def eq(name, got, exp):
    assert str(got) == str(exp), f"[{name}] got={got!r} expected={exp!r}"


# =====================================================================
#  第3問 図形の性質
# =====================================================================
def verify_q3():
    S = ANS[3]

    # --- 三角形パラメータ(問題文の設定を独立に再現) ---
    AB = AC = 10
    BC = 12
    a = BC // 2               # BD=DC=6
    # AD (二等辺の対称軸・BC の垂直二等分線)
    AD = isqrt(AB * AB - a * a)
    assert AD * AD == AB * AB - a * a
    eq("AD(=8)", AD, 8)

    # (ア) 内心 → 直線 BI は ∠ABC を2等分する。選択肢を独立定義し index 照合。
    A_CH = ["直線ACと垂直", "ねじれの位置", "∠ABCを2等分", "ACの中点を通る"]
    eq("ア", circ(A_CH.index("∠ABCを2等分")), S["ア"])

    # (イ,ウ) 角の二等分線定理: AI:ID = BA:BD = AB:a
    ratio = Fraction(AB, a)                  # 10:6 = 5:3
    AI = Fraction(AD) * ratio.numerator / (ratio.numerator + ratio.denominator)
    ID = Fraction(AD) * ratio.denominator / (ratio.numerator + ratio.denominator)
    assert AI.denominator == 1 and ID.denominator == 1
    AI = int(AI); ID = int(ID)
    eq("イ(AI)", AI, S["イ"])
    eq("ウ(ID)", ID, S["ウ"])
    eq("AI:ID既約", f"{AI}:{ID}", "5:3")

    # (エ) 4点 E,I,D,? が同一円周上 → ? = P。選択肢 A/B/C/G/P。
    E_CH = ["A", "B", "C", "G", "P"]
    eq("エ", circ(E_CH.index("P")), S["エ"])

    # (オカ) 方べきの定理: AE·AP = AI·AD
    oka = AI * AD
    eq("オカ(方べき)", str(oka).zfill(2), S["オ"] + S["カ"])
    assert 10 <= oka <= 99, "オカ は2桁でなければならない"

    # --- 座標計算で E,I,D,P の共円性・F=PI∩DE・体積を厳密検証 ---
    # A=(0,0), D=(AD,0), B=(AD,a), C=(AD,-a), I=(AI,0)
    Apt = sp.Matrix([0, 0]); Dpt = sp.Matrix([AD, 0])
    Bpt = sp.Matrix([AD, a]); Cpt = sp.Matrix([AD, -a])
    Ipt = sp.Matrix([AI, 0])
    # G = △IBC の重心
    Gx = sp.Rational(AI + AD + AD, 3)
    assert Gx == 7, Gx
    h = sp.Symbol("h", positive=True)
    Ppt = sp.Matrix([Gx, h])
    AP2 = Gx**2 + h**2
    # E: 方べきで AE=oka/AP, P と同じ向き → E = (oka/AP^2)*P
    Ept = (sp.Rational(oka, 1) / AP2) * Ppt

    # 共円性(E,I,D,P): det=0 が h に依らず成り立つことを確認
    def concyclic_det(pts):
        M = sp.Matrix([[p[0]**2 + p[1]**2, p[0], p[1], 1] for p in pts])
        return sp.simplify(M.det())
    assert concyclic_det([Ept, Ipt, Dpt, Ppt]) == 0, "E,I,D,P が共円でない"
    # 方べき AE·AP=oka を座標で再確認
    AE = sp.sqrt((Ept - Apt).dot(Ept - Apt))
    AP = sp.sqrt((Ppt - Apt).dot(Ppt - Apt))
    assert sp.simplify(AE * AP) == oka

    # F = I + t(P-I) が DE 上 → t(h)
    t = sp.Symbol("t")
    Fpt = Ipt + t * (Ppt - Ipt)
    cross = (Fpt[0] - Dpt[0]) * (Ept[1] - Dpt[1]) - (Fpt[1] - Dpt[1]) * (Ept[0] - Dpt[0])
    tH = sp.simplify(sp.solve(sp.Eq(cross, 0), t)[0])

    area = sp.Rational(1, 2) * BC * AD          # 底面積 △ABC = 48
    assert area == 48

    def solve_from_ratio(ifp_n, ifp_d):
        tval = sp.Rational(ifp_n, ifp_n + ifp_d)
        sols = [s for s in sp.solve(sp.Eq(tH, tval), h) if s.is_real and s > 0]
        return sols[0]

    # 仮定1: IF:FP=3:2
    h1 = solve_from_ratio(3, 2)
    AP1 = sp.sqrt(Gx**2 + h1**2)
    # AP=ケ√コ 形: coeff, radicand
    ap1sq = int(sp.nsimplify(Gx**2 + h1**2))
    coeff, rad = 1, ap1sq
    d = 2
    while d * d <= rad:
        while rad % (d * d) == 0:
            rad //= d * d; coeff *= d
        d += 1
    eq("ケ(AP係数)", coeff, S["ケ"])
    eq("コ(AP根号内)", rad, S["コ"])
    assert all(rad % (k * k) != 0 for k in range(2, isqrt(rad) + 1)), "コ に平方因子"
    assert coeff >= 2 and rad >= 2, "AP=ケ√コ の形が退化"

    # PE:EA
    AE1 = sp.Rational(oka, 1) / AP1
    PE1 = AP1 - AE1
    peea = sp.nsimplify(PE1 / AE1)
    pe, ea = sp.Rational(peea).p, sp.Rational(peea).q
    eq("キ:ク(PE:EA)", f"{pe}:{ea}", f"{S['キ']}:{S['ク']}")
    assert gcd(pe, ea) == 1

    # V1
    V1 = sp.Rational(1, 3) * area * h1
    assert V1.q == 1
    eq("サシ(V1)", str(int(V1)).zfill(2), S["サ"] + S["シ"])

    # 仮定2: IF:FP=3:5
    h2 = solve_from_ratio(3, 5)
    V2 = sp.Rational(1, 3) * area * h2
    assert V2.q == 1
    rV = sp.nsimplify(V2 / V1)               # V2:V1
    sn, se = sp.Rational(rV).p, sp.Rational(rV).q
    eq("ス:セ(V2:V1)", f"{sn}:{se}", f"{S['ス']}:{S['セ']}")
    assert gcd(sn, se) == 1

    # ソ: V2 と V1 の大小 (選択肢: ⓪小 ①等 ②大)
    SO_CH = ["小", "等", "大"]
    rel = "大" if V2 > V1 else ("等" if V2 == V1 else "小")
    eq("ソ(大小)", circ(SO_CH.index(rel)), S["ソ"])


# =====================================================================
#  第4問 場合の数と確率  (全数列挙)
# =====================================================================
P_A = Fraction(1, 3)      # A が各対戦で勝つ確率


def champ_prob(players):
    """総当たり全対戦結果を列挙し、抽選込みで A が優勝する確率を厳密分数で返す。"""
    n = len(players)
    Ai = players.index("A")
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    tot = Fraction(0)
    for out in product([0, 1], repeat=len(pairs)):
        wins = [0] * n
        pr = Fraction(1)
        for bit, (i, j) in zip(out, pairs):
            w = i if bit else j
            wins[w] += 1
            if players[i] == "A":
                pr *= P_A if bit else (1 - P_A)
            elif players[j] == "A":
                pr *= (1 - P_A) if bit else P_A
            else:
                pr *= Fraction(1, 2)
        mx = max(wins)
        top = [k for k in range(n) if wins[k] == mx]
        if Ai in top:
            tot += pr * Fraction(1, len(top))
    return tot


def verify_q4():
    S = ANS[4]
    p, q = P_A, 1 - P_A

    def frac(*kanas):
        """スロット文字列から分数を復元。例 frac('ア','イ')=1/9。"""
        # numerator = 最初の1文字、denominator = 残り連結
        num = int(S[kanas[0]])
        den = int("".join(S[k] for k in kanas[1:]))
        return Fraction(num, den)

    # 全体整合(独立列挙)
    P3 = champ_prob(["A", "B", "C"])
    P4 = champ_prob(["A", "B", "C", "D"])
    assert P3 == Fraction(5, 27), P3
    assert P4 == Fraction(1, 9), P4

    # (1)(i) A2勝0敗
    ai = p * p
    eq("ア/イ", ai, frac("ア", "イ"))

    # (1)(ii) 表2 巴の対戦結果の確率: A→B勝(p), A→C負(q), B→C勝(1/2)
    p_cycle = p * q * Fraction(1, 2)
    eq("ウ/エ", p_cycle, frac("ウ", "エ"))
    # 抽選 3人タイ → 1/3
    lot3 = Fraction(1, 3)
    eq("オ/カ", lot3, frac("オ", "カ"))
    # A1勝1敗優勝 = 2(相手の選び方) × 巴確率 × 抽選
    a11 = 2 * p_cycle * lot3
    eq("キ/クケ", a11, frac("キ", "ク", "ケ"))
    # (1) 合計 = P3
    assert ai + a11 == P3

    # (2)(i) D全敗: D は A に負け(p), B に負け(1/2), C に負け(1/2)
    p_Dlose = p * Fraction(1, 2) * Fraction(1, 2)
    eq("コ/サシ", p_Dlose, frac("コ", "サ", "シ"))
    # 全敗者ありで A2勝1敗優勝 = 3 × (D全敗 × (1)(ii)のA1勝1敗優勝)
    someone_winless = 3 * (p_Dlose * a11)
    eq("ス/セソ", someone_winless, frac("ス", "セ", "ソ"))

    # (2)(ii) ソ相当(タ): A が B に負け C,D に勝つとき、B,C,D の3試合8通りのうち
    #   全敗者なし & A(2勝)が最多タイ となる対戦結果の数
    def count_and_prob():
        cnt = 0
        pr_sum = Fraction(0)
        for bc, bd, cd in product([0, 1], repeat=3):
            w = {"A": 2, "B": 1, "C": 0, "D": 0}
            w["B" if bc else "C"] += 1
            w["B" if bd else "D"] += 1
            w["C" if cd else "D"] += 1
            if min(w.values()) == 0:
                continue
            mx = max(w.values()); top = [k for k in w if w[k] == mx]
            if "A" in top and w["A"] == 2:
                cnt += 1
                pr_sum += Fraction(1, 2) ** 3 * Fraction(1, len(top))
        return cnt, pr_sum
    cnt, pr_sum = count_and_prob()
    eq("タ(場合の数)", cnt, S["タ"])
    # 全敗者なしで A2勝1敗優勝 = 3(A が負ける相手) × [ q*p*p × Σ((1/2)^3 × 抽選) ]
    nobody_winless = 3 * (q * p * p) * pr_sum
    eq("チ/ツテ", nobody_winless, frac("チ", "ツ", "テ"))

    # 4人版 A優勝 = A3勝0敗 + A2勝1敗優勝
    a30 = p * p * p
    total4 = a30 + someone_winless + nobody_winless
    assert total4 == P4, (total4, P4)
    eq("ト/ナ", total4, frac("ト", "ナ"))

    # 3人版との差
    diff = P3 - P4
    eq("ニ/ヌネ", diff, frac("ニ", "ヌ", "ネ"))
    assert diff > 0, "4人版の方が小さいはず"

    # ノ: 4人にすると小さい(⓪)か大きい(①)か
    NO_CH = ["小さい", "大きい"]
    eq("ノ(大小)", circ(NO_CH.index("小さい")), S["ノ"])


# =====================================================================
#  正解位置の分布(選択スロットが偏りすぎない)
# =====================================================================
def verify_distribution():
    circles = "⓪①②③④⑤⑥⑦⑧⑨"
    picks = []
    for sec in (3, 4):
        for k, v in ANS[sec].items():
            if v in circles:
                picks.append((sec, k, circles.index(v)))
    # 各大問内で同一番号3連続していないか(登場順)
    for sec in (3, 4):
        seq = [i for (s, k, i) in picks if s == sec]
        run = 1
        for j in range(1, len(seq)):
            run = run + 1 if seq[j] == seq[j - 1] else 1
            assert run < 3, f"section{sec} で選択番号が3連続"
    from collections import Counter
    cnt = Counter(i for (_, _, i) in picks)
    total = sum(cnt.values())
    assert max(cnt.values()) <= total * 0.6 + 0.5, f"偏り: {cnt} / {total}"
    print(f"  選択スロット分布: {dict(sorted(cnt.items()))} (計{total})")


def verify_slot_layout():
    """SECTIONS 本文のマーク枠と ANS_SECTIONS のキーが完全一致(過不足なし)か検査。"""
    import re
    SLOT = re.compile(r"[〔〚]([ア-ヶ]+)[〕〛]")

    def collect(sec_no):
        keys = []
        for sec in MOD.SECTIONS:
            if sec["no"] != sec_no:
                continue
            for part in sec["parts"]:
                for b in part["blocks"]:
                    text = ""
                    if b["t"] == "p":
                        text = b["text"]
                    elif b["t"] == "m":
                        text = b["tex"]
                    elif b["t"] == "choices" and b.get("for"):
                        text = b["for"]
                    for mkana in SLOT.findall(text):
                        for ch in mkana:
                            keys.append(ch)
        return keys

    for sec_no in (3, 4):
        used = collect(sec_no)
        used_set = set(used)
        ans_set = set(ANS[sec_no].keys())
        missing = ans_set - used_set
        extra = used_set - ans_set
        assert not missing, f"第{sec_no}問: ANSにあるが本文に無いスロット {missing}"
        assert not extra, f"第{sec_no}問: 本文にあるがANSに無いスロット {extra}"
        # 五十音順で連続(ア始まり・欠番なし)
        order = "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホ"
        ordered = [k for k in order if k in ans_set]
        assert ordered == list(order[:len(ordered)]), \
            f"第{sec_no}問: スロットが五十音連続でない {ordered}"
        print(f"  第{sec_no}問 スロット {len(ans_set)}個 (ア〜{ordered[-1]}) 本文と一致")


def main():
    verify_slot_layout()
    verify_q3(); print("第3問 図形の性質 OK")
    verify_q4(); print("第4問 場合の数と確率 OK")
    verify_distribution(); print("正解分布 OK")
    print("ALL VERIFY PASS")


if __name__ == "__main__":
    main()
