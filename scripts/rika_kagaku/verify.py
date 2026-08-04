# -*- coding: utf-8 -*-
"""
中学理科［化学分野］確認プリント 化学固有の数値検算。

★設計:「content に書いてある ans を読んで、それと同じ計算をして OK と言う」のでは検算にならない。
  ここでは _p2.py の**一次定数だけ**（表1の溶解度／Mg:O:MgO の比／表2の質量／
  中和でちょうど緑色になる体積）を取り出し、化学のきまりから**この場でもう一度**計算して、
  content の ans 文字列と突き合わせる。content 側の数値が手打ちで1文字ずれていれば不一致で落ちる。

検算するもの
  大問1 溶解度  … とけ残り／冷やしたとき出てくる固体（水100g・水150gの両方）／
                   質量パーセント濃度（分母＝液全体）／表1のHTMLが定数と同じ数字を出しているか／
                   「塩化ナトリウムは冷やしても出てこない」という問5の前提が表1で成り立つか
  大問2 質量比  … Mg＋O＝MgO（比の内部矛盾）／表2の全列が 3:2:5 に従うか／グラフの打点数／
                   完全に反応したときの生成量／★一部未反応の量（酸素からの式と連立の式の2通りで
                   計算し、両方が一致することまで見る）
  大問3 電気分解… イオンの電気の符号から「どちらの電極に銅が付くか」を導いて選択肢と照合／
                   4つの式の原子の数を数え、つり合っているのが正解の1つだけか
  大問4 中和    … 表3の色を「中性の体積」から再計算／体積の比例（塩酸を変えたとき）／
                   入れすぎた分を打ち消す塩酸（逆向きの比例）／設問が成立する設定か
                   （問2は中性を通りこしているか、問4のビーカーはまだ酸性か）
  全体          … 高校内容（mol・電離度・pHの対数・イオン化傾向・滴定計算）の混入がないか
"""
import re

# 高校で扱う語。中学の問題集に混ざっていないか全文走査する（★中学範囲を超えない、の機械化）
HIGH_SCHOOL_NG = ["mol", "モル", "物質量", "電離度", "アボガドロ", "イオン化傾向",
                  "中和滴定", "規定度", "対数", "水素イオン指数", "平衡", "酸化数"]

_SUB = {"₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4",
        "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9"}


# ---------------------------------------------------------------- 小道具
def _num(s):
    """'67.5g' -> 67.5 / '24%' -> 24.0"""
    m = re.match(r"^[約]?(-?[0-9.]+)", str(s).strip())
    return float(m.group(1)) if m else None


def _close(a, b, tol=1e-6):
    return a is not None and b is not None and abs(a - b) <= tol * max(1.0, abs(b))


def _decimals(s):
    """'3.50g' -> 2 / '77g' -> 0。★数として合っていても「3.5g」と書けば表2（0.30/1.20 …）と
    書式がそろわず、生徒は有効数字を落として書く見本を読むことになる。数だけ見る検算では
    これを見逃す（実際に見逃した）ので、桁の書式もここで見る。"""
    m = re.search(r"\.([0-9]+)", str(s))
    return len(m.group(1)) if m else 0


def _find(C, g, big, *keywords):
    """★設問を番号ではなく設問文のキーワードで引く。小問を1つ挿入しただけで
    ゲートが別の問題を見に行く事故を防ぐ（位置に依存しない参照にしておく）。"""
    blocks = [b for b in C.PART2 if b["no"] == big]
    if not blocks:
        g._fail(f"[ゲート自体の不整合] {big} が見つからない")
        return None, None
    hits = [(i, q) for i, q in enumerate(blocks[0]["qs"], 1)
            if all(k in q["q"] for k in keywords)]
    if len(hits) != 1:
        g._fail(f"[ゲート自体の不整合] {big} でキーワード{keywords}に一致する設問が{len(hits)}件"
                "（0件＝設問文を変えた／2件以上＝キーワードが弱い）")
        return None, None
    return hits[0]


def _cmp(C, g, tag, big, keywords, want, unit="", fmt="{:g}"):
    """独立に再計算した want と、content の ans を突き合わせる。"""
    i, q = _find(C, g, big, *keywords)
    if q is None:
        return False
    got = _num(q["ans"])
    if not _close(got, want):
        g._fail(f"[{tag}] {big}問{i}: 独立再計算＝{fmt.format(want)}{unit} だが解答＝「{q['ans']}」")
        return False
    if unit and not str(q["ans"]).endswith(unit):
        g._fail(f"[{tag}] {big}問{i}: 解答「{q['ans']}」に単位「{unit}」が付いていない")
        return False
    g._ok(f"[{tag}] {big}問{i} 独立再計算＝{fmt.format(want)}{unit} 一致 OK")
    return True


def _choice(C, g, big, keywords):
    """mc の「正解として選ばれている選択肢の文字列」を返す。"""
    i, q = _find(C, g, big, *keywords)
    if q is None:
        return None, None
    if q["type"] != "mc" or not isinstance(q["ans"], int) or not (0 <= q["ans"] < len(q["choices"])):
        g._fail(f"[ゲート自体の不整合] {big}問{i} が mc でない、または ans={q['ans']!r} が"
                "選択肢のレンジ外（★ans は 0 始まりの index）")
        return i, None
    return i, q["choices"][q["ans"]]


def _atoms(side):
    """'2CuCl₂' のような式の片側から、原子の種類ごとの個数を数える。"""
    counts = {}
    for term in re.split(r"[＋+]", side):
        term = term.strip()
        if not term:
            continue
        m = re.match(r"^([0-9]*)(.*)$", term)
        coef = int(m.group(1)) if m.group(1) else 1
        for el, sub in re.findall(r"([A-Z][a-z]?)([₀-₉0-9]*)", m.group(2)):
            n = int("".join(_SUB.get(ch, ch) for ch in sub)) if sub else 1
            counts[el] = counts.get(el, 0) + coef * n
    return counts


def _balanced(eq):
    left, _, right = eq.partition("→")
    return bool(right.strip()) and _atoms(left) == _atoms(right)


# ---------------------------------------------------------------- 本体
def extra(C, g):
    import _p2 as P

    _yokai(C, g, P)
    _shitsuryohi(C, g, P)
    _denki(C, g, P)
    _chuwa(C, g, P)
    _range(C, g)


# ============================================================ 大問1 溶解度
def _yokai(C, g, P):
    t = list(P.SOL_T)
    kno3 = dict(zip(t, P.SOL_KNO3))
    nacl = dict(zip(t, P.SOL_NACL))

    # 表1そのものの妥当性（温度が上がればとける量はふえる／表と設問の温度がそろっている）
    if sorted(kno3) != t or any(kno3[a] >= kno3[b] for a, b in zip(t, t[1:])):
        g._fail(f"[溶解度] 表1の硝酸カリウムが温度順に増えていない: {P.SOL_KNO3}")
    for need, name in ((P.Q1_T, "問1"), (P.Q2_HOT, "問2"), (P.Q2_COLD, "問2"),
                       (P.Q4_HOT, "問4"), (P.Q4_COLD, "問4")):
        if need not in kno3:
            g._fail(f"[溶解度] {name}が使う{need}℃が表1にない（表から読み取れない設問になっている）")
            return

    # 表1のHTMLが、定数と同じ数字を印字しているか（表だけ古いまま、を防ぐ）
    tbl = str([b for b in C.PART2 if b["no"] == "大問1"][0]["figs"][0])
    miss = [str(v) for v in list(P.SOL_KNO3) + list(P.SOL_NACL) + t if str(v) not in tbl]
    if miss:
        g._fail(f"[溶解度] 表1に定数の値 {miss} が印字されていない")
    else:
        g._ok(f"[溶解度] 表1のHTMLが定数（{P.SOL_KNO3}／{P.SOL_NACL}）と一致 OK")

    # 問1 とけ残り＝入れた質量−その温度の限界
    left = P.Q1_ADD_G - kno3[P.Q1_T]
    i, ch = _choice(C, g, "大問1", ("入れてよくかき混ぜた",))
    if ch is not None:
        if left <= 0:
            g._fail(f"[溶解度] 問1は{P.Q1_T}℃で{P.Q1_ADD_G}g入れてもすべてとける設定（とけ残りが出ない）")
        elif f"{left:g}g" not in ch:
            g._fail(f"[溶解度] 大問1問{i}: 独立再計算のとけ残り{left:g}g が正解の選択肢「{ch}」にない")
        else:
            g._ok(f"[溶解度] 大問1問{i} とけ残り {P.Q1_ADD_G}−{kno3[P.Q1_T]}＝{left:g}g 一致 OK")

    # 問2 出てくる固体（水100g）
    out2 = (kno3[P.Q2_HOT] - kno3[P.Q2_COLD]) * P.Q2_WATER / P.SOL_BASE_G
    _cmp(C, g, "溶解度", "大問1", (f"水{P.Q2_WATER}g", "出てくる固体は何gか"), out2, "g")

    # 問3 質量パーセント濃度（分母は液全体）
    solute = kno3[P.Q2_COLD] * P.Q2_WATER / P.SOL_BASE_G
    pct = solute / (P.Q2_WATER + solute) * 100
    _cmp(C, g, "濃度", "大問1", ("質量パーセント濃度",), float(round(pct)), "%")
    if abs(pct - round(pct)) > 0.45:
        g._warn(f"[濃度] 四捨五入の境目に近い値（{pct:.3f}%）。中学生が迷わない数値に選び直すこと")
    # ★分母を水にする典型ミスの答えと一致していないか（一致すると誤答が正解になる）
    if round(pct) == round(solute / P.Q2_WATER * 100):
        g._fail("[濃度] 分母を「水の質量」にしても同じ答えになる設定＝この設問で濃度の理解が測れない")
    else:
        g._ok(f"[濃度] 液全体で割ると{pct:.1f}%／水で割ると"
              f"{solute / P.Q2_WATER * 100:.1f}% と別の値になる（設問が成立）OK")

    # 問4 水の量が100gでないとき
    out4 = (kno3[P.Q4_HOT] - kno3[P.Q4_COLD]) * P.Q4_WATER / P.SOL_BASE_G
    _cmp(C, g, "溶解度", "大問1", (f"水{P.Q4_WATER}g",), out4, "g")
    if P.Q4_WATER == P.SOL_BASE_G:
        g._fail("[溶解度] 問4も水100gのままで、問2と同じ計算になっている（水の量の換算を問えない）")

    # 問5 の前提（塩化ナトリウムは冷やしてもほとんど出てこない）が表1で成り立つか
    d_nacl = nacl[P.Q2_HOT] - nacl[P.Q2_COLD]
    d_kno3 = kno3[P.Q2_HOT] - kno3[P.Q2_COLD]
    if d_nacl >= d_kno3 * 0.2:
        g._fail(f"[溶解度] 塩化ナトリウムの温度による差{d_nacl}g が大きすぎる。"
                "「冷やしても出てこないから水を蒸発させる」という問5の答えが成り立たない")
    else:
        g._ok(f"[溶解度] {P.Q2_HOT}→{P.Q2_COLD}℃の差 硝酸カリウム{d_kno3}g／塩化ナトリウム{d_nacl}g"
              "＝問5「冷やすのではなく蒸発させる」が成立 OK")


# ============================================================ 大問2 質量比
def _shitsuryohi(C, g, P):
    mg, ox, mgo = P.MG_O
    if mg + ox != mgo:
        g._fail(f"[質量比] Mg:O:MgO＝{mg}:{ox}:{mgo} は "
                f"{mg}＋{ox}≠{mgo} で質量保存に反する（比そのものが誤り）")
        return
    if (mg, ox, mgo) == (4, 1, 5):
        g._fail("[質量比] 銅の比(4:1:5)が入っている。この冊子はマグネシウムで作る約束"
                "（銅は rika_enshu/content_no01.py の大問2で既出）")
    g._ok(f"[質量比] Mg:O:MgO＝{mg}:{ox}:{mgo}（{mg}＋{ox}＝{mgo}）内部矛盾なし OK")

    # 表2の全列を比から再計算
    bad = []
    for m, after in zip(P.MG_TABLE, P.MGO_TABLE):
        if abs(after - m * mgo / mg) > 5e-3:
            bad.append(f"{m:.2f}g→{after:.2f}g（正しくは{m * mgo / mg:.2f}g）")
        elif abs((after - m) - m * ox / mg) > 5e-3:
            bad.append(f"{m:.2f}g の酸素 {after - m:.2f}g（正しくは{m * ox / mg:.2f}g）")
    if bad:
        g._fail(f"[質量比] 表2が比{mg}:{ox}:{mgo}に従っていない: " + "／".join(bad))
    else:
        g._ok(f"[質量比] 表2の{len(P.MG_TABLE)}列すべてが {mg}:{ox}:{mgo} に一致 OK")

    b2 = [b for b in C.PART2 if b["no"] == "大問2"][0]
    tbl, fig = str(b2["figs"][0]), str(b2["figs"][1])
    miss = [f"{m:.2f}" for m in list(P.MG_TABLE) + list(P.MGO_TABLE) if f"{m:.2f}" not in tbl]
    if miss:
        g._fail(f"[質量比] 表2に定数の値 {miss} が印字されていない")
    dots, want = fig.count("<circle"), len(P.MG_TABLE) + 1
    if dots != want:
        g._fail(f"[質量比] 図1の打点が{dots}個。表2の{len(P.MG_TABLE)}列＋原点＝{want}個のはず")
    elif max(P.MG_TABLE) > P.MG_GRAPH_XMAX or max(P.MGO_TABLE) > P.MG_GRAPH_YMAX:
        g._fail(f"[質量比] 図1の点が軸の範囲（x≦{P.MG_GRAPH_XMAX}／y≦{P.MG_GRAPH_YMAX}）"
                "からはみ出している")
    else:
        g._ok(f"[質量比] 表2と図1の打点{dots}個（原点込み）が一致・軸範囲内 OK")

    # 問2 質量比（比の文字列そのものを照合。全角コロンのゆれは吸収する）
    i, q = _find(C, g, "大問2", "整数比")
    if q is not None:
        got = str(q["ans"]).replace("：", ":").replace(" ", "")
        if got != f"{mg}:{ox}":
            g._fail(f"[質量比] 大問2問{i}: 独立再計算＝{mg}：{ox} だが解答＝「{q['ans']}」")
        else:
            g._ok(f"[質量比] 大問2問{i} マグネシウム：酸素＝{mg}：{ox} 一致 OK")

    # 問3 完全に反応したときにできる白い物質
    _cmp(C, g, "質量比", "大問2", ("できる白い物質は何gか",),
         P.MG_Q3 * mgo / mg, "g", fmt="{:.2f}")

    # 問4 一部が未反応（★2通りの解き方で計算し、両方一致することまで見る）
    got_ox = P.MG_Q4_AFTER - P.MG_Q4          # ふえた質量＝結びついた酸素
    reacted_a = got_ox * mg / ox              # 解き方1：酸素から比で
    reacted_b = (P.MG_Q4_AFTER - P.MG_Q4) / (mgo / mg - 1)   # 解き方2：連立で
    if not (0 < got_ox and reacted_a < P.MG_Q4):
        g._fail(f"[質量比] 問4の設定が不成立: {P.MG_Q4:.2f}g→{P.MG_Q4_AFTER:.2f}g だと"
                f"反応した分{reacted_a:.2f}g がはじめの質量以上（未反応が残らない）")
        return
    if abs(reacted_a - reacted_b) > 1e-9:
        g._fail(f"[質量比] 問4の2通りの解き方が一致しない（酸素から{reacted_a:.3f}g／"
                f"連立から{reacted_b:.3f}g）")
    left = P.MG_Q4 - reacted_a
    if _cmp(C, g, "質量比", "大問2", ("残っているマグネシウム",), left, "g", fmt="{:.2f}"):
        g._ok(f"[質量比] 大問2問4 酸素{got_ox:.2f}g→反応{reacted_a:.2f}g／未反応{left:.2f}g、"
              "2通りの解き方が一致 OK")
    if abs(left * 100 - round(left * 100)) > 1e-6:
        g._warn(f"[数値設計] 未反応の質量 {left}g が小数第3位まで出る。数値を選び直すこと")

    # ★桁の書式：表2は小数第2位まで（0.30／1.20）。質量を答えさせる設問もそれにそろえる。
    want_d = max(_decimals(f"{m:.2f}") for m in P.MG_TABLE)
    bad_d = []
    for kw in (("できる白い物質は何gか",), ("残っているマグネシウム",)):
        i, q = _find(C, g, "大問2", *kw)
        if q is not None and _decimals(q["ans"]) != want_d:
            bad_d.append(f'問{i}「{q["ans"]}」')
    if bad_d:
        g._fail(f"[桁の書式] 表2は小数第{want_d}位までなのに、解答の桁がそろっていない: "
                + "／".join(bad_d) + "（数は合っていても、有効数字を落とした見本になる）")
    else:
        g._ok(f"[桁の書式] 大問2の質量の解答が表2と同じ小数第{want_d}位までで統一 OK")


# ============================================================ 大問3 電気分解
def _denki(C, g, P):
    # ★イオンの電気の符号から「銅がどちらの電極に付くか」を導き、選択肢と照合する
    if P.CU_ION_SIGN <= 0 or P.CL_ION_SIGN >= 0:
        g._fail("[電気分解] 銅イオンは陽イオン（＋）、塩化物イオンは陰イオン（−）。符号の定数が逆")
        return
    cu_side = P.ELEC_MINUS      # ＋の電気をもつイオンは−極につないだ電極へ引かれる
    cl_side = P.ELEC_PLUS
    i, ch = _choice(C, g, "大問3", ("組み合わせ",))
    if ch is not None:
        want = (f"{cu_side}に赤色", f"{cl_side}から気体")
        if not all(w in ch for w in want):
            g._fail(f"[電気分解] 大問3問{i}: 陽イオンの銅は−極側の電極{cu_side}へ、"
                    f"陰イオンは＋極側の電極{cl_side}へ。正解の選択肢「{ch}」がこれと合わない")
        else:
            g._ok(f"[電気分解] 大問3問{i} 銅は電極{cu_side}（−極側）・気体は電極{cl_side}"
                  "（＋極側）を符号から再導出 一致 OK")

    # ★4つの式の原子の数を数え、つり合っているのが「正解の1つだけ」か
    j, q = _find(C, g, "大問3", "表した式")
    if q is not None:
        ok = [k for k, c in enumerate(q["choices"]) if _balanced(c)]
        if ok != [q["ans"]]:
            g._fail(f"[化学変化の式] 大問3問{j}: 原子の数がつり合う式は "
                    f"{[q['choices'][k] for k in ok] or 'なし'}。"
                    f"正解に指定されているのは「{q['choices'][q['ans']]}」"
                    "（つり合う式が0個＝正解なし／2個以上＝正解が1つに決まらない）")
        else:
            g._ok(f"[化学変化の式] 大問3問{j} 原子を数え直し、つり合うのは正解の"
                  f"「{q['choices'][q['ans']]}」だけ（{_atoms(q['choices'][q['ans']].split('→')[0])}）OK")

    # 問4：どちらのイオンも電極で取り出されるので、両方が減る
    k, ch4 = _choice(C, g, "大問3", ("イオンの数について",))
    if ch4 is not None:
        if "どちらも減" not in ch4:
            g._fail(f"[電気分解] 大問3問{k}: 銅イオンは金属になり、塩化物イオンは気体になるので"
                    f"どちらも減る。正解の選択肢「{ch4}」がこれと合わない")
        else:
            g._ok(f"[電気分解] 大問3問{k} 両方のイオンが電極で取り出される＝どちらも減る OK")


# ============================================================ 大問4 中和
def _chuwa(C, g, P):
    added = list(P.NAOH_ADDED)
    if P.NAOH_NEUTRAL not in added:
        g._fail(f"[中和] ちょうど緑色になる体積{P.NAOH_NEUTRAL}cm³ が表3の{added}にない"
                "（表から読み取れない設問になっている）")
        return
    if not (min(added) < P.NAOH_NEUTRAL < max(added)):
        g._fail("[中和] 表3に、緑色より前（酸性）と後（アルカリ性）の両方がそろっていない")

    # 表3の色を「中性の体積」から再計算し、印字されている色と突き合わせる
    tbl = str([b for b in C.PART2 if b["no"] == "大問4"][0]["figs"][0])
    want = ["黄色" if v < P.NAOH_NEUTRAL else ("緑色" if v == P.NAOH_NEUTRAL else "青色")
            for v in added]
    got = re.findall(r"黄色|緑色|青色", tbl)
    if got != want:
        g._fail(f"[中和] 表3の色 {got} が、中性＝{P.NAOH_NEUTRAL}cm³ からの再計算 {want} と不一致")
    else:
        g._ok(f"[中和] 表3の色 {want} を中性{P.NAOH_NEUTRAL}cm³ から再計算 一致 OK")

    ratio = P.NAOH_NEUTRAL / P.HCL_V           # 塩酸1cm³ を打ち消す水酸化ナトリウム水溶液
    # 問1 塩酸の体積を変えたとき、必要な体積は比例する
    need = P.N_Q1_HCL * ratio
    _cmp(C, g, "中和", "大問4", ("何cm³ 必要か",), need, "cm³")
    if abs(need * 10 - round(need * 10)) > 1e-9:
        g._warn(f"[数値設計] 問1の答え{need}cm³ が小数第2位まで出る。数値を選び直すこと")

    # 問2 入れすぎた分を打ち消すのに必要な塩酸（逆向きの比例）
    over = P.N_Q2_NAOH - P.NAOH_NEUTRAL
    if over <= 0:
        g._fail(f"[中和] 問2は{P.N_Q2_NAOH}cm³ 加えた設定だが、中性は{P.NAOH_NEUTRAL}cm³。"
                "通りこしていないので「青色になった」も「塩酸を加える」も成り立たない")
    else:
        _cmp(C, g, "中和", "大問4", ("あと何cm³",), over / ratio, "cm³")
        g._ok(f"[中和] 問2 入れすぎ{over}cm³ ÷ 比{ratio:g} ＝ {over / ratio:g}cm³ "
              f"（塩酸の合計{P.HCL_V + over / ratio:g}cm³ ＝ {P.N_Q2_NAOH}cm³ とつり合う）OK")
        # つり合いの検算：合計した塩酸と、加えた水酸化ナトリウム水溶液が過不足なく打ち消し合うか
        if abs((P.HCL_V + over / ratio) * ratio - P.N_Q2_NAOH) > 1e-9:
            g._fail("[中和] 問2の答えを足しても、加えた水酸化ナトリウム水溶液と過不足なく"
                    "打ち消し合わない（比例の立式が誤り）")

    # 問4 のビーカーが「まだ酸が残っている（黄色）」設定か
    idx = P.BEAKERS.index(P.N_Q4_BEAKER) if P.N_Q4_BEAKER in P.BEAKERS else -1
    if idx < 0:
        g._fail(f"[中和] 問4のビーカー{P.N_Q4_BEAKER}が表3にない")
    elif added[idx] >= P.NAOH_NEUTRAL:
        g._fail(f"[中和] 問4のビーカー{P.N_Q4_BEAKER}は{added[idx]}cm³ 加えた液＝"
                f"中性{P.NAOH_NEUTRAL}cm³ 以上。酸が残っておらず「気体が発生する」が成り立たない")
    else:
        k, ch = _choice(C, g, "大問4", ("マグネシウムリボン",))
        if ch is not None and "気体が発生" not in ch:
            g._fail(f"[中和] 大問4問{k}: ビーカー{P.N_Q4_BEAKER}はまだ酸性なので気体が発生する。"
                    f"正解の選択肢「{ch}」がこれと合わない")
        else:
            g._ok(f"[中和] 問4 ビーカー{P.N_Q4_BEAKER}は{added[idx]}cm³＜中性{P.NAOH_NEUTRAL}cm³"
                  "＝まだ酸性→気体が発生 OK")

    # 問5 で塩ができているのは「ちょうど緑色になったビーカー」でなければ論点がぼやける
    m, q5 = _find(C, g, "大問4", "できるしくみ")
    if q5 is not None:
        neutral_beaker = P.BEAKERS[added.index(P.NAOH_NEUTRAL)]
        if neutral_beaker not in q5["q"]:
            g._fail(f"[中和] 大問4問{m}: 中性になったのはビーカー{neutral_beaker}なのに、"
                    "設問がそのビーカーを指していない")
        else:
            g._ok(f"[中和] 大問4問{m} 中性のビーカー{neutral_beaker}を指している OK")


# ============================================================ 全体 中学範囲
def _range(C, g):
    """★高校内容の混入を機械で見る（設問文・選択肢・解説・途中式まで全部）。"""
    buf = []

    def walk(o):
        if isinstance(o, str):
            buf.append(o)
        elif isinstance(o, dict):
            for v in o.values():
                walk(v)
        elif isinstance(o, (list, tuple)):
            for v in o:
                walk(v)

    walk(C.PART2)
    text = " ".join(buf)
    hit = [w for w in HIGH_SCHOOL_NG if w in text]
    if hit:
        g._fail(f"[中学範囲] 高校内容の語が第2部に混ざっている: {hit}")
    else:
        g._ok(f"[中学範囲] 高校内容の語（{len(HIGH_SCHOOL_NG)}語）の混入なし OK")
