# -*- coding: utf-8 -*-
"""
中学理科 演習 機械ゲート（build.py が先に実行し、FAIL ならビルドを中止する）

  A. 汎用6ゲート …… scripts/_workbook_gates.py を import（社会No.01の事故から作った共有部品）
     解答の自己漏洩／正解肢が最長のテル／記述の文末と問いの対応／解説の①②③④参照ズレ／
     正解位置の偏り／記述の字数（機械数え直し）／文字監査
  B. 理科固有 …… ★content の答えを一切見ずに、物理・化学の法則からPythonで独立に再計算して照合する
     ・オームの法則（直列/並列の合成抵抗・電流・電圧）
     ・定比例の法則（銅の酸化。表・グラフ・未反応の問題まで）
     ・透明半球（弧の長さ→時刻）／南中高度（90°−緯度）
     ・表とグラフが同じ数値から作られているか（表だけ直してグラフが古いまま、を防ぐ）
     ・単位の付け忘れ／有効数字
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))   # scripts/ を通す
sys.path.insert(0, HERE)

from _workbook_gates import Gate            # noqa: E402
import content_no01 as C                    # noqa: E402

g = Gate()


def q_of(no, i):
    """大問noのi番目(1始まり)の設問"""
    b = [x for x in C.PART2 if x["no"] == no][0]
    return b["qs"][i - 1]


def q_find(no, *keywords):
    """★設問を「番号」ではなく「設問文のキーワード」で引く。
    番号決め打ちにすると、あとから小問を1つ挿入しただけで全部のゲートが別の問題を見に行く
    （実際そうなった）。位置に依存しない参照にしておくこと。"""
    b = [x for x in C.PART2 if x["no"] == no][0]
    hits = [(i, q) for i, q in enumerate(b["qs"], 1)
            if all(k in q["q"] for k in keywords)]
    if len(hits) != 1:
        g._fail(f"[ゲート自体の不整合] {no} でキーワード{keywords}に一致する設問が{len(hits)}件"
                "（0件=設問文を変えた／2件以上=キーワードが弱い）")
        return None, None
    return hits[0]


# ---------------------------------------------------------------- B-1 オームの法則
def check_ohm():
    E, R1, R2 = C.E, C.R1, C.R2
    ser_R = R1 + R2
    ser_I = E / ser_R
    par_I = E / R1 + E / R2
    par_R = E / par_I
    exp = {1: f"{ser_R:g}Ω", 2: f"{ser_I:.2f}A", 3: f"{par_I:.2f}A", 4: f"{par_R:g}Ω"}
    for i, want in exp.items():
        got = q_of("大問1", i)["ans"]
        if got != want:
            g._fail(f"[オームの法則] 大問1問{i}: 独立再計算={want} だが解答={got}")
        else:
            g._ok(f"[オーム] 大問1問{i} 独立再計算={want} 一致 OK")
    # 直列の分圧が電源電圧に戻るか（物理的整合）
    if abs(ser_I * R1 + ser_I * R2 - E) > 1e-9:
        g._fail("[オームの法則] 直列の分圧の和が電源電圧に一致しない")
    # 並列の合成抵抗は最小の抵抗より小さいはず（解説の主張の検算）
    if not par_R < min(R1, R2):
        g._fail(f"[オームの法則] 並列の合成抵抗{par_R}Ωが最小抵抗{min(R1,R2)}Ω以上＝解説が成立しない")
    else:
        g._ok(f"[オーム] 並列合成{par_R:g}Ω < 最小抵抗{min(R1,R2)}Ω（解説の主張が成立）OK")
    # 割り切れない数字を出題していないか（中学生が扱えるか）
    for v, name in ((ser_I, "直列の電流"), (par_I, "並列の電流"), (par_R, "並列の合成抵抗")):
        if abs(v * 100 - round(v * 100)) > 1e-9:
            g._warn(f"[数値設計] {name}={v} が小数第3位まで出る。中学向けに数値を選び直すこと")


# ---------------------------------------------------------------- B-2 定比例の法則
def check_teihirei():
    cu, o, cuo = C.CU_O
    # 表がすべて同じ比になっているか（1行でもズレたら定比例の設問が壊れる）
    for m, mo in zip(C.CU_TABLE, C.CUO_TABLE):
        if abs(mo - m * cuo / cu) > 1e-9:
            g._fail(f"[定比例] 表1が比{cu}:{cuo}に従っていない: 銅{m}g → 酸化銅{mo}g "
                    f"(正しくは{m*cuo/cu:.2f}g)")
        ox = mo - m
        if abs(ox - m * o / cu) > 1e-9:
            g._fail(f"[定比例] 銅{m}g の酸素が比に合わない: {ox:.2f}g "
                    f"(正しくは{m*o/cu:.2f}g)")
    g._ok(f"[定比例] 表1の{len(C.CU_TABLE)}行すべてが Cu:O:CuO={cu}:{o}:{cuo} に一致 OK")

    # 「銅の質量→酸化銅の質量」を問う設問（設問文の数値から独立に解く）
    i2, q2 = q_find("大問2", "十分に加熱したとき", "酸化銅は何g")
    if q2:
        m = float(re.search(r"(\d+\.\d+)gの銅", q2["q"]).group(1))
        want2 = f"{m*cuo/cu:.2f}g"
        if q2["ans"] != want2:
            g._fail(f"[定比例] 大問2問{i2}: 独立再計算={want2} だが解答={q2['ans']}")
        else:
            g._ok(f"[定比例] 大問2問{i2} 銅{m}g→独立再計算={want2} 一致 OK")

    # 「未反応の銅」を問う設問
    i3, q3 = q_find("大問2", "反応せずに残っている銅")
    if not q3:
        return
    nums = [float(x) for x in re.findall(r"(\d+\.\d+)g", q3["q"])]
    if len(nums) < 2:
        g._fail(f"[定比例] 大問2問{i3}の設問文から数値を読み取れない（書式変更?）")
        return
    total_cu, after = nums[0], nums[1]
    # 反応した銅 x: (cuo/cu)x + (total_cu - x) = after
    x = (after - total_cu) / (cuo / cu - 1)
    left = total_cu - x
    want3 = f"{left:.2f}g"
    if q3["ans"] != want3:
        g._fail(f"[定比例] 大問2問{i3}: 独立再計算={want3} だが解答={q3['ans']}")
    else:
        g._ok(f"[定比例] 大問2問{i3} 独立再計算: 反応した銅{x:.2f}g/未反応{want3} 一致 OK")
    # 解説の検算（酸素から解く別解）が同じ答えになるか
    ox = after - total_cu
    if abs(ox * cu / o - x) > 1e-9:
        g._fail(f"[定比例] 大問2問{i3}の別解(酸素{ox:.2f}g から逆算)が本解と一致しない")
    else:
        g._ok(f"[定比例] 大問2問{i3} 別解(酸素{ox:.2f}g×{cu}/{o})も同じ{x:.2f}g OK")


# ---------------------------------------------------------------- B-3 天体
def check_tentai():
    h = C.SUN_FIRST_H - C.SUN_TO_RISE / C.SUN_CM_PER_H
    if abs(h - round(h)) > 1e-9:
        g._fail(f"[天体] 日の出時刻が{h}時と半端。cm設定を中学生向けに選び直すこと")
    want = f"{int(h)}時00分"
    got = q_of("大問4", 2)["ans"]
    if got != want:
        g._fail(f"[天体] 大問4問2: 独立再計算={want} だが解答={got}")
    else:
        g._ok(f"[天体] 大問4問2 日の出 独立再計算={want} 一致 OK")

    n = 90 - C.LAT
    wn = f"{n}度"
    if q_of("大問4", 3)["ans"] != wn:
        g._fail(f"[天体] 大問4問3: 春分の南中高度は90−{C.LAT}={wn} だが解答="
                f"{q_of('大問4',3)['ans']}")
    else:
        g._ok(f"[天体] 大問4問3 南中高度 独立再計算={wn} 一致 OK")
    if not 0 < n < 90:
        g._fail(f"[天体] 南中高度{n}°が物理的にありえない")

    # ★以前ここは figs[0]（描画済みSVG文字列）に対して "hemisphere([" を正規表現で探しており、
    #   永久にマッチしないうえ結果を使わず無条件で OK を出す死にコードだった。
    #   図に渡す角度列を content 側の定数 SUN_DOTS に切り出し、その定数を直接検査する。
    angs = [a for a, _ in C.SUN_DOTS]
    diffs = {round(b - a, 6) for a, b in zip(angs, angs[1:])}
    if diffs != {15.0}:
        g._fail(f"[天体] 図4の点の間隔が15°で揃っていない: {sorted(diffs)}°"
                "（地球の自転＝1時間15°という問1の根拠が崩れる）")
    else:
        g._ok(f"[天体] 図4 点{len(angs)}個の間隔がすべて15° OK（1時間＝15°）")
    # 最初の点の角度 = 日の出からの経過時間 × 15°（日の出＝0°＝真東）
    elapsed = _rise_int(C)
    if angs[0] != elapsed * 15:
        g._fail(f"[天体] 図4の最初の点{angs[0]}°が、日の出からの経過{elapsed}時間"
                f"（={elapsed*15}°）と合わない")
    else:
        g._ok(f"[天体] 図4 最初の点{angs[0]}° = 日の出から{elapsed}時間ぶん OK")

    # ★南中点の「高さ」が南中高度と一致しているか（実際に踏んだ事故）
    #   hemisphere が点を輪郭と同じ半径に置いていたため、南中(90°)が天頂＝高度90°に描かれ、
    #   「北緯35°・春分＝55°」という問3の答えと図が真っ向から矛盾していた。
    if abs(C.SUN_NANCHU - n) > 1e-9:
        g._fail(f"[天体] 図4に描く南中高度 SUN_NANCHU={C.SUN_NANCHU}° が"
                f"問3の答え{n}°と一致しない（図と解答が矛盾する）")
    else:
        g._ok(f"[天体] 図4の南中高度{C.SUN_NANCHU}° = 解答{n}° 一致 OK（天頂90°に描いていない）")


def _rise_int(C):
    return int(round(C.SUN_TO_RISE / C.SUN_CM_PER_H))


# ---------------------------------------------------------------- B-4 表とグラフの一致
def check_table_graph_sync():
    """表1の数値とグラフ(図3)の打点が同じ配列から作られているか。
    片方だけ直して古い図が残る事故を防ぐ。"""
    b = [x for x in C.PART2 if x["no"] == "大問2"][0]
    svg = str(b["figs"][1])
    tbl = str(b["figs"][0])
    miss = [f"{m:.2f}" for m in C.CU_TABLE if f"{m:.2f}" not in tbl]
    if miss:
        g._fail(f"[表/図] 表1に銅の質量 {miss} が出ていない")
    # グラフの打点数 = 原点 + 表の行数
    dots = svg.count("<circle")
    want = len(C.CU_TABLE) + 1
    if dots != want:
        g._fail(f"[表/図] 図3の打点が{dots}個。表1の{len(C.CU_TABLE)}行＋原点＝{want}個のはず")
    else:
        g._ok(f"[表/図] 表1({len(C.CU_TABLE)}行)と図3の打点({dots}個=原点込み)が一致 OK")


# ---------------------------------------------------------------- B-5 単位
def check_units():
    bad = []
    for b in C.PART2:
        for i, q in enumerate(b["qs"], 1):
            if q["type"] != "calc":
                continue
            ans = q["ans"]
            if re.fullmatch(r"[\d.]+", ans):
                bad.append(f'{b["no"]}問{i}「{ans}」')
            if not q.get("work"):
                g._fail(f'{b["no"]}問{i} は計算問題だが work（式）が無い')
    if bad:
        g._fail("[単位] 計算問題の解答に単位が付いていない: " + "／".join(bad))
    else:
        g._ok("[単位] 計算問題の解答すべてに単位または記号あり OK")


# ---------------------------------------------------------------- B-6 作図が壊れていないか
def check_figures():
    """★実際に踏んだ事故: BASE_CSS の svg.fg 指定が入っておらず、回路図の配線が全部消え、
    ラベルだけが巨大に描画された（viewBoxが拡大されるため）。PDFのテキスト監査では
    「文字はある」ので素通りする＝画像を見るまで気づけない。CSSと図の要素数を機械で検査する。"""
    import build_common as B

    need = ["svg.fg {", "svg.fg text", "svg.fg .wire", "svg.fg .grid",
            ".figrow {", ".figcell {", ".figcap {"]
    miss = [n for n in need if n not in B.BASE_CSS]
    if miss:
        g._fail(f"[作図CSS] BASE_CSS に必須指定が無い（線が消えて文字が巨大化する）: {miss}")
    else:
        g._ok(f"[作図CSS] svg.fg / figrow の指定{len(need)}件すべて存在 OK")

    # 各図が「線」と「文字」の両方を持っているか（片方だけ＝描画が壊れている）
    for b in C.PART2:
        for k, fig in enumerate(b.get("figs", []), 1):
            s = str(fig)
            if "<svg" not in s:
                continue
            wires = s.count('class="wire"') + s.count("<polyline") + s.count("<line")
            texts = s.count("<text")
            if wires == 0:
                g._fail(f"[作図] {b['no']} の図{k} に線が1本も無い（描画ロジックの破損）")
            elif texts == 0:
                g._fail(f"[作図] {b['no']} の図{k} に文字が無い（ラベルの欠落）")
            else:
                g._ok(f"[作図] {b['no']} 図{k}: 線{wires}本／文字{texts}個 OK")

    # 回路図は「電池1個 + 抵抗2個 + 閉じた導線」が揃っているか
    c = B.circuit("series")
    if c.count("<rect") < 2:
        g._fail("[作図] 直列回路図に抵抗器が2つ描かれていない")
    p = B.circuit("parallel")
    if p.count("<rect") < 2:
        g._fail("[作図] 並列回路図に抵抗器が2つ描かれていない")
    # ★並列図に「左端から右端まで水平に貫くむき出しの導線」があるとショート回路になる
    #   （実際に描いてしまい、抵抗を素通りする経路ができた）
    import re as _re
    L, R = 22, 230 - 22
    short = [d for d in _re.findall(r'class="wire" d="([^"]+)"', p)
             if _re.fullmatch(rf"M{L} \d+ H{R}", d.strip())]
    if short:
        g._fail(f"[作図] 並列回路図に抵抗を通らない導線がある＝ショート回路: {short}")
    else:
        g._ok("[作図] 並列回路図にショート経路なし／抵抗器2個 OK")


# ---------------------------------------------------------------- 配点
def check_points():
    n1 = sum(len(x["items"]) for x in C.PART1)
    p2 = sum(b["point"] for b in C.PART2)
    p3 = len(C.PART3) * 3
    tot = n1 + p2 + p3
    if tot != C.META["total"]:
        g._fail(f"[配点] 第1部{n1}＋第2部{p2}＋第3部{p3}＝{tot} ≠ META {C.META['total']}")
    else:
        g._ok(f"[配点] 第1部{n1}点＋第2部{p2}点＋第3部{p3}点＝{tot}点 OK")
    for b in C.PART2:
        pts = [q.get("pt") for q in b["qs"]]
        if not all(pts) or sum(pts) != b["point"]:
            g._fail(f"[配点] {b['no']} 小問{pts} 合計{sum(x or 0 for x in pts)} != {b['point']}")
        else:
            g._ok(f"[配点] {b['no']} 小問{pts} 合計{sum(pts)} = {b['point']} OK")


# ---------------------------------------------------------------- 実行
def main():
    print("=== 中学理科 演習 No.01 機械ゲート ===")
    import json
    qa = [{"q": it["q"], "ans": it["ans"]} for x in C.PART1 for it in x["items"]]
    mcs = [{"where": f'{b["no"]}問{i}', "choices": q["choices"], "ans": q["ans"],
            "exp": q.get("exp", "")}
           for b in C.PART2 for i, q in enumerate(b["qs"], 1) if q["type"] == "mc"]
    descs = ([{"where": f'{b["no"]}問{i}', "q": q["q"], "ans": q["ans"], "limit": q["limit"]}
              for b in C.PART2 for i, q in enumerate(b["qs"], 1) if q["type"] == "desc"]
             + [{"where": f"記述{i}", "q": q["q"], "ans": q["ans"], "limit": q["limit"]}
                for i, q in enumerate(C.PART3, 1)])
    # 問題編に印字される「一問一答以外の全テキスト」
    printed = " ".join([
        json.dumps([{k: v for k, v in b.items() if k != "figs"} for b in C.PART2],
                   ensure_ascii=False),
        " ".join(str(f) for b in C.PART2 for f in b.get("figs", [])),
        " ".join(q["q"] for q in C.PART3),
    ])

    print("[A] 汎用ゲート（scripts/_workbook_gates.py）")
    # ★第1部どうしの漏洩((11)沸点→(12)の設問文 等)は printed に第1部の設問文を
    #   入れていなかったため構造的に検出できなかった。min_len も理科では2字が主力。
    g.answer_leak(qa, printed, min_len=2,
                  allow={"抵抗": "「電気抵抗」の略称。大問1で回路用語として不可避に登場する"})
    g.longest_tell(mcs)
    g.choice_position(mcs)
    g.exp_choice_refs(mcs)
    g.desc_ending(descs)
    g.char_limit(descs)
    g.keys_consistency(descs)
    g.glyphs([C.META, C.POINTS, C.PART1, C.PART3,
              [{k: v for k, v in b.items() if k != "figs"} for b in C.PART2]])

    print("[B] 理科固有（法則からの独立再計算）")
    check_ohm()
    check_teihirei()
    check_tentai()
    check_table_graph_sync()
    check_units()
    check_figures()
    check_points()
    g.report()


if __name__ == "__main__":
    main()
