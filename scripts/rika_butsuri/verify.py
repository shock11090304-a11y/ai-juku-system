# -*- coding: utf-8 -*-
"""
中学理科［物理分野］確認プリント No.01　物理固有の数値検算（check.py が extra() を呼ぶ）

★設計: **_p2.py が計算した結果（I_A・WORK_J…）を読んで「合っている」と言っても意味がない。**
  ここでは _p2.py の「一次定数」（焦点距離・物体の高さ・電源電圧・抵抗・水の量・打点数・
  質量・高さ・時間など、実験の設定値）だけを取り出し、物理の式で **この場でもう一度**
  計算して、content の ans 文字列と突き合わせる。
  _p2.py の導出コードや派生定数を手で書きかえた事故も、ここで不一致として落ちる。

■ 独立に再計算するもの
  オームの法則    Ｉ ＝ Ｖ ÷ Ｒ                        （大問2問1）
  電力            Ｐ ＝ Ｖ × Ｉ と Ｐ ＝ Ｖ² ÷ Ｒ の2通りで一致するか（大問2問2）
  電力量・熱量    Ｑ ＝ Ｐ × 時間〔秒〕                （大問2問3。分→秒の直し忘れも落ちる）
  水が得た熱量    Ｑ ＝ 4.2 × 水の質量 × 上がった温度  （★上昇温度は図2の点列から読み直す）
                  → さらに **水の熱量 ＜ 電力量** の向きまで確かめる
                     （逆向きだと大問2問4「熱がにげた理由」という設問自体が成立しない）
  平均の速さ      ｖ ＝ 距離 ÷ 時間                    （大問3問1・問2）
  速さの増え方    Δｖ ＝ となり合うテープの長さの差 ÷ テープ1本の時間（大問3問3）
  仕事            Ｗ ＝ Ｆ × ｓ                        （大問4問1）
  仕事率          Ｐ ＝ Ｗ ÷ ｔ                        （大問4問2）
  仕事の原理      直接／動滑車／斜面 の3通りで 力×距離 がすべて等しいか（大問4問3・問5）
  凸レンズ        表1をレンズの式から作り直して一致するか／中学の型
                  （2倍の位置＝同じ大きさ／2倍より遠い＝小さい像／焦点と2倍の間＝大きい像／
                    焦点の内側＝実像なし）／相似（像の高さ÷物体の高さ ＝ 像まで÷物体まで）

■ 4択は「番号」でなく **選ばれた文の中身** を見る
  ans は0始まりindexなので、1始まりで書くと全問1つずれる（本リポジトリで3回起きている）。
  そこで choices[ans] が物理的に正しい文言を含むか、かつ他の選択肢が同じ文言を含まないか
  （＝正解が一意か）を機械で確かめる。番号の照合では絶対に見つからない事故を拾う層。

■ 解答欄の単位・高校内容の混入もここで見る
  calc の unit が物理量と合っているか（「答 ___ W」の欄に電流を書かせていないか）。
  加速度・運動方程式・力積・三角比・レンズの公式などの語が
  第1部〜第3部・ポイント整理のどこかに紛れこんでいないか（中学の範囲を超えない）。
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import _p2 as P  # noqa: E402

NUM = re.compile(r"(-?\d+(?:\.\d+)?)")

# 中学の範囲外の語。設問文・選択肢だけでなく解説・ポイント整理も走査する
BANNED_HS = ["加速度", "運動方程式", "力積", "運動量", "三角比", "三角関数",
             "レンズの公式", "写像公式", "ｓｉｎ", "ｃｏｓ", "ｔａｎ"]


def _num(s):
    """'2700J' -> 2700.0 ／ '48cm/s' -> 48.0 ／ '0.1秒' -> 0.1"""
    m = NUM.search(str(s))
    return float(m.group(1)) if m else None


def _walk(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for v in o.values():
            yield from _walk(v)
    elif isinstance(o, (list, tuple)):
        for v in o:
            yield from _walk(v)


def _block(C, no):
    for b in C.PART2:
        if b["no"] == no:
            return b
    return None


def _qn(C, no, i):
    """大問 no の i 問目（1始まり）。構成が変わっていたら None。"""
    b = _block(C, no)
    if not b or len(b["qs"]) < i:
        return None
    return b["qs"][i - 1]


class _Ctx:
    """検算の結果をためる。通った項目数を最後に1行で出す。"""

    def __init__(self, g):
        self.g = g
        self.ok = 0

    def fail(self, msg):
        self.g._fail("[検算] " + msg)

    def calc(self, where, q, want, unit, tol=5e-3):
        """calc 小問：模範解答の数値と独立計算 want を突き合わせ、解答欄の単位も見る。"""
        if q is None:
            return self.fail(f"{where} が見つからない（小問の並びが変わっている）")
        if q.get("type") != "calc":
            return self.fail(f"{where} が calc ではない（type={q.get('type')}）")
        got = _num(q.get("ans"))
        if got is None:
            return self.fail(f"{where} 模範解答「{q.get('ans')}」から数値が読めない")
        if abs(got - want) > tol:
            return self.fail(f"{where} 模範解答「{q['ans']}」≠ 独立計算 {want:g}{unit}")
        if unit and str(q.get("unit", "")).strip() != unit:
            return self.fail(f"{where} 解答欄の単位「{q.get('unit')}」が物理量と合わない"
                             f"（正しくは {unit}）")
        self.ok += 1

    def mc(self, where, q, must):
        """4択：選ばれた選択肢が must を全部含み、他の選択肢は含まない（正解が一意）か。"""
        if q is None:
            return self.fail(f"{where} が見つからない（小問の並びが変わっている）")
        if q.get("type") != "mc":
            return self.fail(f"{where} が mc ではない（type={q.get('type')}）")
        ch, a = q["choices"], q["ans"]
        if not isinstance(a, int) or not (0 <= a < len(ch)):
            return self.fail(f"{where} ans={a} が選択肢のレンジ外（★ans は0始まりindex）")
        if not all(k in ch[a] for k in must):
            return self.fail(f"{where} 選ばれた選択肢「{ch[a]}」が物理的に正しい内容"
                             f"（{'／'.join(must)}）になっていない"
                             "（★0始まりindexを1始まりで書いた事故を疑う）")
        dup = [c for i, c in enumerate(ch) if i != a and all(k in c for k in must)]
        if dup:
            return self.fail(f"{where} 正解と同じ内容の選択肢がもう1つある: 「{dup[0]}」")
        self.ok += 1

    def near(self, where, got, want, tol=1e-6):
        if got is None or abs(got - want) > tol:
            return self.fail(f"{where}: {got} ≠ 独立計算 {want:g}")
        self.ok += 1


# ---------------------------------------------------------------- 大問1 凸レンズと像
def _lens(C, c):
    f, H = P.LENS_F, P.OBJ_H

    # (a) 表1そのものを作り直す（content の LENS_B / LENS_H と突き合わせる）
    b_re = [round(1.0 / (1.0 / f - 1.0 / a), 1) for a in P.LENS_A]
    h_re = [round(H * b / a, 1) for a, b in zip(P.LENS_A, b_re)]
    if b_re != list(P.LENS_B) or h_re != list(P.LENS_H):
        c.fail(f"表1が再計算と不一致: 像の位置 {list(P.LENS_B)} vs {b_re}／"
               f"像の高さ {list(P.LENS_H)} vs {h_re}")
    else:
        c.ok += 1
        c.g._ok(f"[検算] 表1（像の位置{b_re}cm・高さ{h_re}cm）を焦点距離{f:g}cmから再計算 一致 OK")

    # (b) 各列が中学の型（2倍の位置／それより遠い／焦点と2倍の間）どおりか
    for a, b, h in zip(P.LENS_A, P.LENS_B, P.LENS_H):
        if a <= f:
            c.fail(f"表1に物体距離{a}cm（焦点距離{f:g}cm以下）の列がある。"
                   "焦点の内側ではスクリーンに像はできないので表として成立しない")
            continue
        if abs(h - H * b / a) > 0.06:      # 相似（中学で使う関係）。表は0.1cmまるめ
            c.fail(f"表1の像の高さ{h}cmが相似の関係と合わない"
                   f"（{H:g}×{b:g}÷{a:g}＝{H*b/a:.2f}cm）")
            continue
        if abs(a - 2 * f) < 1e-9:
            ng = abs(b - 2 * f) > 1e-6 or abs(h - H) > 1e-6
            msg = f"焦点距離の2倍（{a}cm）なのに像が2倍の位置・同じ大きさになっていない"
        elif a > 2 * f:
            ng = not (f < b < 2 * f) or not (h < H)
            msg = f"焦点距離の2倍より遠い（{a}cm）のに像が小さくなっていない"
        else:
            ng = not (b > 2 * f) or not (h > H)
            msg = f"焦点と焦点距離の2倍の間（{a}cm）なのに像が大きくなっていない"
        if ng:
            c.fail(f"{msg}（スクリーンまで{b}cm・像の高さ{h}cm）")
        else:
            c.ok += 1

    # (c) 問2：焦点距離を「表から」中学の型だけで求め直す
    same = [a for a, h in zip(P.LENS_A, P.LENS_H) if abs(h - H) < 1e-6]
    if len(same) != 1:
        c.fail(f"像の高さが物体と同じ{H:g}cmになる列が{len(same)}個。"
               "焦点距離が表から一意に決まらないので問2に答えが定まらない")
    else:
        f_tbl = same[0] / 2.0                       # 「同じ大きさ＝2倍の位置」→ 半分が焦点距離
        c.near(f"大問1問2 表から求めた焦点距離{f_tbl:g}cm", f_tbl, f)
        c.calc("大問1問2", _qn(C, "大問1", 2), f_tbl, "cm")
        # 物体距離とスクリーン距離が等しい列からも同じ値になるか（別ルートの二重確認）
        pair = [b for a, b in zip(P.LENS_A, P.LENS_B) if abs(a - b) < 1e-9]
        if len(pair) != 1 or abs(pair[0] / 2.0 - f_tbl) > 1e-9:
            c.fail("物体距離＝スクリーン距離の列から求めた焦点距離が、"
                   "像の高さから求めた焦点距離と一致しない")
        else:
            c.ok += 1

    # (d) 問3：追加条件が同じレンズで成り立つか → 相似で像の高さ
    A, B = P.LENS_Q3_A, P.LENS_Q3_B
    f3 = 1.0 / (1.0 / A + 1.0 / B)
    if abs(f3 - f) > 1e-6:
        c.fail(f"問3の条件（物体まで{A}cm・スクリーンまで{B}cm）は焦点距離{f3:.3f}cmを意味し、"
               f"表1の{f:g}cmと矛盾する（設問が成立しない）")
    else:
        c.calc("大問1問3", _qn(C, "大問1", 3), H * B / A, "cm")

    # (e) 問1：スクリーンにできるのは実像 → 上下も左右も逆向き
    c.mc("大問1問1", _qn(C, "大問1", 1), ["上下も左右も", "逆向き"])

    # (f) 問4：焦点の内側 → 実像はできず、正立で拡大された虚像が見える
    if not (P.LENS_INSIDE < f):
        c.fail(f"問4の位置{P.LENS_INSIDE}cmが焦点距離{f:g}cmの内側になっていない"
               "（この設定ではスクリーンに実像ができてしまう）")
    else:
        c.mc("大問1問4", _qn(C, "大問1", 4), ["大きく", "同じ向き"])


# ---------------------------------------------------------------- 大問2 電流による発熱
def _heat(C, c):
    V, R = P.V_HEAT, P.R_A
    cur = V / R                                  # オームの法則 I＝V÷R
    pw = V * cur                                 # 電力 P＝V×I
    c.near("大問2 電力を P＝VI と P＝V²/R の2通りで計算", pw, V * V / R, 1e-9)
    sec = P.HEAT_MIN * 60
    elec = pw * sec                              # 電力量〔J〕＝P×秒

    c.calc("大問2問1", _qn(C, "大問2", 1), cur, "A")
    c.calc("大問2問2", _qn(C, "大問2", 2), pw, "W")
    c.calc("大問2問3", _qn(C, "大問2", 3), elec, "J")

    # 派生定数そのものの検算（手で書きかえられていないか）
    c.near("大問2 定数 I_A", P.I_A, cur, 1e-6)
    c.near("大問2 定数 P_A", P.P_A, pw, 1e-6)
    c.near("大問2 定数 WATT_SEC_A", P.WATT_SEC_A, elec, 1e-6)

    # 図2の点列を作り直し、そこから上昇温度を読んで水が得た熱量を独立に計算する
    pts = [(m, round(P.T_START + P.RISE_PER_MIN * m, 1)) for m in range(P.HEAT_MIN + 1)]
    if pts != list(P.HEAT_POINTS):
        c.fail(f"図2の点列 {list(P.HEAT_POINTS)} が"
               f"「はじめの水温＋上昇率×時間」{pts} と不一致")
    elif max(y for _, y in pts) > P.GRAPH_YMAX or max(x for x, _ in pts) > P.GRAPH_XMAX:
        c.fail(f"図2の点が軸範囲（x≦{P.GRAPH_XMAX}／y≦{P.GRAPH_YMAX}）からはみ出す")
    else:
        c.ok += 1

    rise = P.HEAT_POINTS[-1][1] - P.HEAT_POINTS[0][1]    # グラフから読んだ上昇温度〔℃〕
    q_water = P.C_WATER * P.WATER_G * rise               # 水が得た熱量〔J〕
    c.near("大問2 定数 Q_WATER", P.Q_WATER, q_water, 1e-6)
    if not (0 < q_water < elec):
        c.fail(f"水が得た熱量{q_water:g}Jが電力量{elec:g}J以上。"
               "大問2問4（電力量より小さい理由を答える設問）が物理的に成り立たない")
    else:
        c.ok += 1
        c.g._ok(f"[検算] 水が得た熱量{q_water:g}J ＜ 電力量{elec:g}J"
                f"（水にわたった割合{q_water/elec*100:.0f}%）＝問4が成り立つ OK")
    q4 = _qn(C, "大問2", 4)
    if q4 is None or f"{q_water:g}J" not in q4.get("q", ""):
        c.fail(f"大問2問4の設問文に、再計算した水の熱量 {q_water:g}J が印字されていない")
    else:
        c.ok += 1

    # 問5：同じ電圧なら電力は抵抗に反比例。抵抗が半分の電熱線Ｂは何倍になるか
    if not (P.R_B < P.R_A):
        c.fail("電熱線Ｂの抵抗が電熱線Ａ以上。問5（Ｂのほうが速く上がる）が成り立たない")
    else:
        ratio = (V * V / P.R_B) / (V * V / P.R_A)
        c.mc("大問2問5", _qn(C, "大問2", 5), [f"{ratio:g}倍"])


# ---------------------------------------------------------------- 大問3 記録タイマーと運動
def _tape(C, c):
    dt = P.TICKS_PER_TAPE / P.TICK_HZ           # テープ1本ぶんの時間〔秒〕
    lens = [round(P.TAPE_FIRST + P.TAPE_STEP * i, 1) for i in range(len(P.TAPE_NAMES))]
    if lens != list(P.TAPE_LEN):
        c.fail(f"表2のテープ長 {list(P.TAPE_LEN)} が再計算 {lens} と不一致")
        return
    c.ok += 1

    diffs = [round(lens[i + 1] - lens[i], 6) for i in range(len(lens) - 1)]
    if not diffs or max(diffs) - min(diffs) > 1e-6:
        c.fail(f"となり合うテープの長さの差が一定でない（{diffs}）。"
               "大問3問3（速さが一定の割合で増える）が成り立たない")
        return
    c.ok += 1

    c.calc("大問3問1", _qn(C, "大問3", 1), dt, "秒")
    c.calc("大問3問2", _qn(C, "大問3", 2), lens[1] / dt, "cm/s")     # 平均の速さ＝距離÷時間
    c.calc("大問3問3", _qn(C, "大問3", 3), diffs[0] / dt, "cm/s")    # 速さの増え方

    c.near("大問3 定数 TAPE_DT", P.TAPE_DT, dt, 1e-6)
    c.near("大問3 定数 TAPE_V_B", P.TAPE_V_B, lens[1] / dt, 1e-6)
    c.near("大問3 定数 TAPE_DV", P.TAPE_DV, diffs[0] / dt, 1e-6)

    # 再計算した長さが、表2にそのまま印字されているか
    fig = " ".join(_block(C, "大問3").get("figs", []))
    missing = [f"{v:.1f}" for v in lens if f"{v:.1f}" not in fig]
    if missing:
        c.fail(f"表2に印字されていないテープの長さがある: {missing}")
    else:
        c.ok += 1

    # 問4：傾きを大きくすると速さの増え方が大きくなる → 長さの差も大きくなる
    c.mc("大問3問4", _qn(C, "大問3", 4), ["差が大きくなる"])


# ---------------------------------------------------------------- 大問4 仕事とエネルギー
def _work(C, c):
    weight = P.MASS_G / 100.0 * P.N_PER_100G     # 重さ〔N〕（100gで1N）
    w = weight * P.LIFT_H                        # 仕事 W＝F×s
    power = w / P.LIFT_SEC                       # 仕事率 P＝W÷t
    f_pul, s_pul = weight / 2.0, P.LIFT_H * 2.0  # 動滑車：力は半分・距離は2倍
    f_slp = w / P.SLOPE_L                        # 斜面：仕事の原理から

    c.calc("大問4問1", _qn(C, "大問4", 1), w, "J")
    c.calc("大問4問2", _qn(C, "大問4", 2), power, "W")
    c.calc("大問4問3", _qn(C, "大問4", 3), f_pul, "N")

    c.near("大問4 定数 WEIGHT_N", P.WEIGHT_N, weight, 1e-6)
    c.near("大問4 定数 WORK_J", P.WORK_J, w, 1e-6)
    c.near("大問4 定数 POWER_W", P.POWER_W, power, 1e-6)
    c.near("大問4 定数 F_PULLEY", P.F_PULLEY, f_pul, 1e-6)
    c.near("大問4 定数 S_PULLEY", P.S_PULLEY, s_pul, 1e-6)
    c.near("大問4 定数 F_SLOPE", P.F_SLOPE, f_slp, 1e-6)

    # ★仕事の原理：直接持ち上げる／動滑車／斜面 の3通りで 力×距離 が等しいか
    works = {"直接": weight * P.LIFT_H, "動滑車": f_pul * s_pul, "斜面": f_slp * P.SLOPE_L}
    if max(works.values()) - min(works.values()) > 1e-6:
        c.fail("仕事の原理が成り立たない: "
               + "／".join(f"{k}{v:g}J" for k, v in works.items()))
    else:
        c.ok += 1
        c.g._ok(f"[検算] 仕事の原理 直接{weight:g}N×{P.LIFT_H:g}m／"
                f"動滑車{f_pul:g}N×{s_pul:g}m／斜面{f_slp:g}N×{P.SLOPE_L:g}m "
                f"＝ 3通りとも{w:g}J OK")
    if not (P.SLOPE_L > P.LIFT_H and f_slp < weight and f_pul < weight):
        c.fail("動滑車や斜面を使っても力が小さくなっていない"
               f"（重さ{weight:g}N／動滑車{f_pul:g}N／斜面{f_slp:g}N・"
               f"高さ{P.LIFT_H}m／斜面{P.SLOPE_L}m）")
    else:
        c.ok += 1

    # 問4：物体を支える力は上向き・動いた向きは水平 → 力の向きに動かした距離が0なので仕事も0J
    # ★力学的エネルギーの保存は第3部の記述7で問うので、この大問では扱わない（二重出題の回避）。
    if not (P.CARRY_L > 0):
        c.fail(f"問4で水平に運ぶ距離が{P.CARRY_L}m（0以下）。"
               "「動かしても仕事は0J」という設問が成り立たない")
    else:
        c.ok += 1
        c.mc("大問4問4", _qn(C, "大問4", 4), ["垂直", "0J"])


# ---------------------------------------------------------------- 高校内容の混入
def _no_highschool(C, c):
    hit = []
    for name in ("PART1", "PART2", "PART3", "POINTS"):
        for s in _walk(getattr(C, name, [])):
            for w in BANNED_HS:
                if w in s:
                    hit.append(f"{name}「{w}」")
    hit = sorted(set(hit))
    if hit:
        c.fail("中学の範囲を超える語が入っている（高校内容は出さない）: " + "／".join(hit))
    else:
        c.ok += 1


# ---------------------------------------------------------------- entry point
def extra(C, g):
    c = _Ctx(g)
    _lens(C, c)
    _heat(C, c)
    _tape(C, c)
    _work(C, c)
    _no_highschool(C, c)
    g._ok(f"[検算] 定数から独立に再計算した照合 {c.ok}項目 OK"
          "（オームの法則／P＝VI／Q＝Pt／速さ＝距離÷時間／W＝Fs／仕事率／仕事の原理／"
          "凸レンズの型・相似／4択は中身で照合）")


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(HERE))
    from _workbook_gates import Gate           # noqa: E402
    import content_no01 as _C                  # noqa: E402
    _gate = Gate()
    extra(_C, _gate)
    _gate.report()
