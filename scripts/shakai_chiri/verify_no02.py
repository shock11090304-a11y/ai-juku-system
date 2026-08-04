# -*- coding: utf-8 -*-
"""
中学社会 地理演習 No.02　地理固有の独立検算（check_no02.py から extra(C, g) が呼ばれる）。

★方針：_p2_no02.py が計算した結果を信用しない。
  **実際に問題編へ印字される表のHTMLを読み直して数値を取り出し**、
  そこから縮尺・時差・構成比・割合を「このファイルに別途書いた式」で計算し直して ans と照合する。
  （_p2_no02 の定数をそのまま使うと「同じ式を2回実行しただけ」になり、検査にならない）

  V0 一次情報   ★表に印字された統計が、下の PUB_*（出典を見て別に書き写した値）と一致するか
  V1 構成比      表2の各行の％の合計が100（±0.5）か／各％が「部門の億円 ÷ 総額 × 100」と一致するか
  V2 縮尺        表3の地図上の長さ × 縮尺の分母 ＝ 実際の長さ を再計算して大問3問1・問2の ans と照合
  V3 傾斜        表3から「標高差 ÷ 実際の水平距離」を計算し、大問3問3の正解番号と照合
  V4 時差        表4の「東経／西経◯度」を読み取って経度差÷15を再計算し、大問4問1・問2・問3と照合
  V5 統計の整合  表1（人口・面積・GNI）から人口密度と大問1問2の4つの主張を再計算
  V6 年で動く表現 「◯位」「最も多い」など、年で入れかわる順位表現が問題編に出ていないか（WARN）
  V7 出典        表の note に年次と出典が書かれているか（WARN）

★V0 を足した理由（2026-08 の突然変異テストで判明）
  はじめは V1〜V5 だけだった。ところが _p2_no02.py の統計の定数をわざと壊しても
  ALL PASS のままだった。表も解答もその定数から生成されるので、
  両方が同じだけずれて「つじつまが合ってしまう」からである。
  ＝ 式の再計算だけでは**データの誤りは1件も捕まらない**。
  そこで、一次情報を見て別に書き写した値（PUB_*）を突き合わせる層を足した。
  ここを直すときは、必ず出典のページを開いて数字を確認してから書きかえること。
  突然変異12件のうち11件を検出する。残る1件は「表3（地形図）の数値の書きかえ」で、
  表3は作問のためにこちらで決めた数値であり外部に正解が無いため、原理的に検出できない
  （長さを変えても、縮尺の式で解答が追随するだけで、問題として正しいまま）。
"""
import os
import re
import sys
import datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

from _workbook_check import printed_text  # noqa: E402

TAG = re.compile(r"<[^>]+>")

# ---------------------------------------------------------------- V0 一次情報の転記
# ★_p2_no02.py を見ずに、出典のページ／PDFを開いて書き写した値。
#   ここと _p2_no02.py の両方を同時に同じだけ間違えないかぎり、データの誤りは検出される。
#
# 農林水産省「令和5年 農業産出額及び生産農業所得（都道府県別）」
#   （農林水産省「都道府県別農林水産業の概要 令和7年版」各県ページ／2026-08 確認）
#   総額（億円）と、同資料が公表している 米・野菜・果実・畜産 の構成比（％）
PUB_PREF_TOTAL = {"新潟県": 2281, "山梨県": 1192, "高知県": 1128, "宮崎県": 3720}
PUB_PREF_PCT = {
    "新潟県": (55.0, 14.8, 3.8, 22.1),
    "山梨県": (5.3, 11.5, 69.7, 7.6),
    "高知県": (9.1, 62.5, 11.6, 8.5),
    "宮崎県": (3.9, 18.8, 4.0, 66.7),
}
# 帝国書院「世界の統計」W01面積／W02人口（Demographic Yearbook2023ほか・2023年）
#   W03人口密度／W67 1人あたりGNI（世界銀行Web・2023年）。2026-08 確認。
PUB_AREA_KM2 = {"ブラジル": 8510417, "オーストラリア": 7692024,
                "大韓民国（韓国）": 100444, "サウジアラビア": 2206714}
PUB_POP_MAN = {"ブラジル": 21628, "オーストラリア": 2664,
               "大韓民国（韓国）": 5171, "サウジアラビア": 3217}
PUB_DENSITY = {"ブラジル": 25, "オーストラリア": 3,
               "大韓民国（韓国）": 515, "サウジアラビア": 15}
PUB_GNI = {"ブラジル": 9070, "オーストラリア": 63140,
           "大韓民国（韓国）": 35490, "サウジアラビア": 28690}
# 各都市が標準時としている子午線（東経＋／西経−）
PUB_LON = {"東京": 135, "カイロ": 30, "ロサンゼルス": -120, "サンパウロ": -45}

# ---------------------------------------------------------------- 年で動く表現の走査（V6）
# 統計の「順位」は年で入れかわるので設問にしてはいけない。
# 一方「最も適切な」「傾斜が最も急な」は年で動かない（定義・幾何の話）ので除外する。
# 「小数第1位まで求めよ」は四捨五入の指示であって順位ではない（誤検出するので先に消す）。
RANK_ALLOW = ("最も適切", "最も近い", "最も急", "最も簡単")
RANK_ALLOW_RE = (r"小数第[0-9０-９]+位", r"第[0-9０-９]+位まで")
RANK_PAT = ("順位", "ランキング", "上位", "シェア",
            "最も多い", "最も大きい", "最も少ない", "最も小さい",
            "最も高い", "最も低い", "最も長い", "最も広い", "最もさかん",
            "全国一", "日本一", "世界一", "トップ")
RANK_NUM = re.compile(r"第?[0-9０-９]+\s*位")


def _cells(table_html):
    """stat_table() が返したHTMLから、行ごとのセル文字列を取り出す。"""
    rows = []
    for tr in re.findall(r"<tr>(.*?)</tr>", table_html, re.S):
        cells = [TAG.sub("", c).strip()
                 for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", tr, re.S)]
        if cells:
            rows.append(cells)
    return rows


def _num(s):
    return float(str(s).replace(",", "").strip())


def _fig(block, idx=0):
    return block["figs"][idx]


def _blk(C, no):
    for b in C.PART2:
        if b["no"] == no:
            return b
    raise KeyError(no)


def _q(C, no, i):
    return _blk(C, no)["qs"][i - 1]


def _ans_num(q):
    """'約831億円' -> 831.0 ／ '1,000m' -> 1000.0"""
    m = re.search(r"[-+]?[0-9][0-9,]*(?:\.[0-9]+)?", str(q["ans"]))
    return float(m.group(0).replace(",", "")) if m else None


def _jp_time(d):
    """datetime -> '8月10日 午前3時'（このファイルで独立に書いた表記ルール）。"""
    tag = "午前" if d.hour < 12 else "午後"
    hh = d.hour - 12 if d.hour >= 12 else d.hour
    out = "%d月%d日 %s%d時" % (d.month, d.day, tag, hh)
    if d.minute:
        out += "%d分" % d.minute
    return out


def extra(C, g):
    import _p2_no02 as P2

    # ============================================================ V0 一次情報との突き合わせ
    n = 0
    for mark, name, total, rice, veg, fruit, live in P2.PREF:
        if name not in PUB_PREF_TOTAL:
            g._fail(f"[一次情報] 表2の「{name}」は転記した一次情報に無い（出典を確認して足すこと）")
            continue
        if total != PUB_PREF_TOTAL[name]:
            g._fail(f"[一次情報] {name}の農業産出額 {total}億円 ≠ 出典 {PUB_PREF_TOTAL[name]}億円")
        for label, got, want in zip(("米", "野菜", "果実", "畜産"),
                                    (rice, veg, fruit, live), PUB_PREF_PCT[name]):
            calc = round(got * 100.0 / total, 1)
            if abs(calc - want) > 0.05:
                g._fail(f"[一次情報] {name}の{label} {got}億円 → {calc}％ だが、"
                        f"出典が公表している構成比は {want}％")
        n += 1
    g._ok(f"[一次情報] 農業産出額 {n}県 億円→構成比 が農林水産省の公表値と一致 OK")

    n = 0
    for mark, name, pop, area, gni, _exp in P2.WORLD:
        if name not in PUB_POP_MAN:
            g._fail(f"[一次情報] 表1の「{name}」は転記した一次情報に無い")
            continue
        if pop != PUB_POP_MAN[name]:
            g._fail(f"[一次情報] {name}の人口 {pop}万人 ≠ 出典 {PUB_POP_MAN[name]}万人")
        if gni != PUB_GNI[name]:
            g._fail(f"[一次情報] {name}の一人あたりGNI {gni}ドル ≠ 出典 {PUB_GNI[name]}ドル")
        want_area = round(PUB_AREA_KM2[name] / 10000.0, 1)
        if abs(area - want_area) > 0.05:
            g._fail(f"[一次情報] {name}の面積 {area}万km² ≠ 出典 "
                    f"{PUB_AREA_KM2[name]:,}km²（＝{want_area}万km²）")
        # 出典の人口・面積から人口密度を出し、出典が公表している人口密度と合うか
        dens = PUB_POP_MAN[name] * 10000.0 / PUB_AREA_KM2[name]
        if abs(dens - PUB_DENSITY[name]) > max(1.0, PUB_DENSITY[name] * 0.01):
            g._fail(f"[一次情報] {name}の人口÷面積＝{dens:.1f}人/km² が、"
                    f"出典の人口密度 {PUB_DENSITY[name]}人/km² と食い違う（転記ミスの疑い）")
        n += 1
    g._ok(f"[一次情報] 世界 {n}か国 人口・面積・GNI・人口密度が出典と一致 OK")

    for city, deg in P2.CITY:
        if PUB_LON.get(city) != deg:
            g._fail(f"[一次情報] {city}の標準時子午線 {deg}度 ≠ 出典 {PUB_LON.get(city)}度")
    g._ok(f"[一次情報] 標準時子午線 {len(P2.CITY)}都市 OK")

    # ============================================================ V1 構成比
    rows = _cells(P2._T2)
    head, body = rows[0], rows[1:]
    if len(body) != len(P2.PREF):
        g._fail(f"[構成比] 表2の行数{len(body)}が PREF の{len(P2.PREF)}件と合わない")
    ok = 0
    for r, src in zip(body, P2.PREF):
        mark, name, total, rice, veg, fruit, live = src
        if r[0] != mark:
            g._fail(f"[構成比] 表2の行の記号がずれている: 表「{r[0]}」/ データ「{mark}」")
            continue
        if _num(r[1]) != total:
            g._fail(f"[構成比] {mark} 表2の農業産出額{r[1]}が データ{total}と違う")
        pcts = [_num(x) for x in r[2:7]]
        s = sum(pcts)
        if abs(s - 100.0) > 0.5:
            g._fail(f"[構成比] {mark}（{name}）の内訳の合計が {s:.1f}％（100％±0.5 から外れる）")
        # 独立に「部門の億円 ÷ 総額 × 100」を計算し直す（その他＝総額−4部門）
        other = total - (rice + veg + fruit + live)
        if other < 0:
            g._fail(f"[構成比] {mark}（{name}）4部門の合計が総額をこえている")
        want = [round(x * 100.0 / total, 1) for x in (rice, veg, fruit, live, other)]
        for col, (a, b) in enumerate(zip(pcts, want)):
            if abs(a - b) > 0.05:
                g._fail(f"[構成比] {mark}（{name}）{head[col+2]} 表の{a}％ ≠ 再計算{b}％")
        ok += 1
    g._ok(f"[構成比] 表2 {ok}県 内訳の合計100％・各％の再計算 OK")

    # 大問2問2（総額×構成比＝部門の産出額）を、表のセルから独立に再計算
    q = _q(C, "大問2", 2)
    tgt = [r for r in body if r[0] == "Ｄ"][0]
    want = round(_num(tgt[1]) * _num(tgt[4]) / 100.0)      # tgt[4] ＝ 果実（％）
    got = _ans_num(q)
    if got != want:
        g._fail(f"[構成比] 大問2問2 独立再計算={want}億円 だが解答は「{q['ans']}」")
    else:
        g._ok(f"[構成比] 大問2問2 {tgt[1]}×{tgt[4]}％＝{want}億円 独立再計算 OK")

    # ============================================================ V2/V3 縮尺・傾斜
    seg = _cells(P2._T3)[1:]                                # [区間, 地図上cm, 標高差m]
    S1, S2 = 25000, 50000                                   # 縮尺の分母（定義。データではない）

    q = _q(C, "大問3", 1)
    name = re.search(r"区間([^\s、はの]+)", q["q"]).group(1)
    row = [r for r in seg if r[0] == name][0]
    want = _num(row[1]) * S1 / 100.0                        # cm→cm→m
    got = _ans_num(q)
    if got != want:
        g._fail(f"[縮尺] 大問3問1 {row[1]}cm×{S1}÷100＝{want:g}m だが解答は「{q['ans']}」")
    elif "m" not in str(q["ans"]):
        g._fail(f"[縮尺] 大問3問1 の解答に単位mが無い: 「{q['ans']}」")
    else:
        g._ok(f"[縮尺] 大問3問1 {row[1]}cm → {want:g}m 独立再計算 OK")

    q = _q(C, "大問3", 2)
    real_m = float(re.search(r"([0-9]+(?:\.[0-9]+)?)m", q["q"]).group(1))
    want = real_m * 100.0 / S2
    got = _ans_num(q)
    if got is None or abs(got - want) > 1e-9:
        g._fail(f"[縮尺] 大問3問2 {real_m}m＝{real_m*100:g}cm ÷{S2}＝{want:g}cm "
                f"だが解答は「{q['ans']}」")
    else:
        g._ok(f"[縮尺] 大問3問2 {real_m:g}m → {want:g}cm 独立再計算 OK")

    q = _q(C, "大問3", 3)
    slopes = [_num(r[2]) / (_num(r[1]) * S1 / 100.0) for r in seg]
    want = slopes.index(max(slopes))
    if sorted(slopes)[-1] == sorted(slopes)[-2]:
        g._fail("[傾斜] 表3に傾斜が同じ区間が2つあり、大問3問3の正解が1つに決まらない")
    if q["choices"] != [r[0] for r in seg]:
        g._fail("[傾斜] 大問3問3の選択肢が表3の区間と一致していない")
    if q["ans"] != want:
        g._fail(f"[傾斜] 大問3問3 独立再計算では{seg[want][0]}（{max(slopes):.4f}）が最も急だが、"
                f"解答は{q['choices'][q['ans']]}")
    else:
        g._ok(f"[傾斜] 大問3問3 {seg[want][0]} が最も急（"
              + "／".join(f"{r[0]}:{s:.3f}" for r, s in zip(seg, slopes)) + "）OK")

    # ============================================================ V4 時差
    lon = {}
    for r in _cells(P2._T4)[1:]:
        m = re.match(r"(東経|西経)([0-9]+)度", r[1])
        if not m:
            g._fail(f"[時差] 表4の子午線が読み取れない: 「{r[1]}」")
            continue
        lon[r[0]] = (1 if m.group(1) == "東経" else -1) * int(m.group(2))
    if len(lon) < 4:
        g._fail("[時差] 表4から4都市ぶんの経度が読み取れなかった")

    def diff(a, b):
        """a から見て b が何時間ずれているか（bが東なら＋）。"""
        return (lon[b] - lon[a]) / 15.0

    q = _q(C, "大問4", 1)
    pair = [c for c in lon if c in q["q"]]
    if len(pair) != 2:
        g._fail(f"[時差] 大問4問1 の設問文から2都市を特定できない: 「{q['q']}」")
    else:
        want = abs(diff(pair[0], pair[1]))
        got = _ans_num(q)
        if got != want:
            g._fail(f"[時差] 大問4問1 経度差{abs(lon[pair[0]]-lon[pair[1]])}度÷15＝{want:g}時間 "
                    f"だが解答は「{q['ans']}」")
        else:
            g._ok(f"[時差] 大問4問1 {pair[0]}−{pair[1]} ＝ {want:g}時間 独立再計算 OK")

    # 問2：基準都市の日時から3都市の現地日時を再計算し、語群の選択肢と突き合わせる
    q = _q(C, "大問4", 2)
    base_city, base_dt = P2.MATCH_BASE
    pool = {}
    for p in q["pool"]:
        k, v = re.split(r"[　\s]+", p, 1)
        pool[k] = v.strip()
    bad = []
    for city, mark in zip(P2.MATCH_CITIES, q["ans"]):
        want = _jp_time(base_dt + dt.timedelta(hours=diff(base_city, city)))
        if pool.get(mark) != want:
            bad.append(f"{city}: 独立再計算「{want}」/ 解答「{mark}＝{pool.get(mark)}」")
    if bad:
        g._fail("[時差] 大問4問2 の組み合わせが独立再計算と違う: " + "／".join(bad))
    else:
        g._ok("[時差] 大問4問2 3都市の現地日時 独立再計算 OK（"
              + "／".join(f"{c}:{pool[m]}" for c, m in zip(P2.MATCH_CITIES, q["ans"])) + "）")
    if len(set(pool.values())) != len(pool):
        g._fail("[時差] 大問4問2 の語群に同じ日時が2つある")

    # 問3：出発時刻＋飛行時間−時差＝到着地の日時
    q = _q(C, "大問4", 3)
    dep, hours = P2.FLIGHT["dep"], P2.FLIGHT["hours"]
    m = re.search(r"([0-9]+)月([0-9]+)日の午前([0-9]+)時", q["q"])
    hh = re.search(r"([0-9]+)時間かけて", q["q"])
    if not m or not hh:
        g._fail(f"[時差] 大問4問3 の設問文から出発日時・飛行時間を読み取れない: 「{q['q']}」")
    else:
        if (int(m.group(1)), int(m.group(2)), int(m.group(3))) != (dep.month, dep.day, dep.hour):
            g._fail("[時差] 大問4問3 の設問文の出発日時が FLIGHT の値と食い違う")
        if int(hh.group(1)) != hours:
            g._fail("[時差] 大問4問3 の設問文の飛行時間が FLIGHT の値と食い違う")
        arr = (dt.datetime(2026, int(m.group(1)), int(m.group(2)), int(m.group(3)))
               + dt.timedelta(hours=int(hh.group(1)))
               + dt.timedelta(hours=diff(P2.FLIGHT["from"], P2.FLIGHT["to"])))
        want = _jp_time(arr)
        if str(q["ans"]).strip() != want:
            g._fail(f"[時差] 大問4問3 独立再計算「{want}」≠ 解答「{q['ans']}」")
        else:
            g._ok(f"[時差] 大問4問3 出発＋{hours}時間−{abs(diff(*[P2.FLIGHT['from'], P2.FLIGHT['to']])):g}時間"
                  f" ＝ {want} 独立再計算 OK")

    # 問4：日付変更線（西→東は1日もどす）
    q = _q(C, "大問4", 4)
    m = re.search(r"([0-9]+)月([0-9]+)日であったとき", q["q"])
    if not m:
        g._fail("[日付変更線] 大問4問4 の設問文からこえる直前の日付を読み取れない")
    else:
        want = "%d月%d日" % (int(m.group(1)), int(m.group(2)) - 1)   # 西→東 は1日もどす
        if str(q["choices"][q["ans"]]).strip() != want:
            g._fail(f"[日付変更線] 大問4問4 西から東へこえる → {want} のはずだが、"
                    f"正解は「{q['choices'][q['ans']]}」")
        else:
            g._ok(f"[日付変更線] 大問4問4 西→東で1日もどす → {want} OK")

    # ============================================================ V5 表1の統計
    w = _cells(P2._T1)[1:]                                  # [記号,人口,面積,GNI,輸出品]
    d = {r[0]: r for r in w}
    q = _q(C, "大問1", 3)
    mark = re.search(r"表1の(.)の国", q["q"]).group(1)
    want = round(_num(d[mark][1]) / _num(d[mark][2]), 1)     # 万人 ÷ 万km² ＝ 人/km²
    got = _ans_num(q)
    if got != want:
        g._fail(f"[人口密度] 大問1問3 {d[mark][1]}÷{d[mark][2]}＝{want}人 だが解答は「{q['ans']}」")
    else:
        g._ok(f"[人口密度] 大問1問3 {mark}＝{want}人/km² 独立再計算 OK")

    # 大問1問2：4つの主張を表1の数値から独立に真偽判定し、正解だけが真かを確かめる
    q = _q(C, "大問1", 2)
    truth = [
        _num(d["Ｄ"][3]) > _num(d["Ａ"][3]) * 3,          # ＤのGNIはＡの3倍をこえる
        _num(d["Ｃ"][2]) > _num(d["Ｂ"][2]) / 10,         # Ｃの面積はＢの10分の1より広い
        _num(d["Ａ"][1]) < sum(_num(x[1]) for x in w) / 2,  # Ａの人口は4か国合計の半分未満
        _num(d["Ｂ"][3]) > _num(d["Ｃ"][3]) * 2,          # ＢのGNIはＣの2倍をこえる
    ]
    if len(q["choices"]) != len(truth):
        g._fail("[統計読み取り] 大問1問2 の選択肢数が検算式の数と合っていない（式を直すこと）")
    elif sum(truth) != 1:
        g._fail(f"[統計読み取り] 大問1問2 表1の数値では正しい文が{sum(truth)}個ある"
                "（1つに決まらない）")
    elif not truth[q["ans"]]:
        g._fail(f"[統計読み取り] 大問1問2 独立再計算では{truth.index(True)+1}番目の文が正しいが、"
                f"解答は{q['ans']+1}番目")
    else:
        g._ok("[統計読み取り] 大問1問2 4つの主張を表1から再計算 → 正解1つだけ OK")

    # 大問1問1・大問2問1：語群と正解の対応が1対1か（同じ記号を2回使っていないか）
    for no, i in (("大問1", 1), ("大問2", 1), ("大問3", 4), ("大問4", 2)):
        qq = _q(C, no, i)
        marks = [re.split(r"[　\s]+", p, 1)[0] for p in qq["pool"]]
        if len(set(qq["ans"])) != len(qq["ans"]):
            g._fail(f"[語群] {no}問{i} 同じ記号を2回答えさせている: {qq['ans']}")
        if any(a not in marks for a in qq["ans"]):
            g._fail(f"[語群] {no}問{i} 語群に無い記号が解答にある: {qq['ans']} / 語群{marks}")
        if len(qq["ans"]) != len(qq["slots"]):
            g._fail(f"[語群] {no}問{i} 解答の数{len(qq['ans'])}と欄の数{len(qq['slots'])}が違う")
    g._ok("[語群] match 4問 記号の重複・語群外・欄数 OK")

    # ============================================================ V6 年で動く表現
    ptxt = printed_text(C)
    scan = ptxt
    for a in RANK_ALLOW:
        scan = scan.replace(a, "　")
    for pat in RANK_ALLOW_RE:
        scan = re.sub(pat, "　", scan)
    hit = [p for p in RANK_PAT if p in scan]
    if RANK_NUM.search(scan):
        hit.append(RANK_NUM.search(scan).group(0))
    if hit:
        g._warn("[年で動く表現] 問題編に順位・シェアの表現がある（統計は年で入れかわるので"
                "設問にしない）: " + "／".join(hit))
    else:
        g._ok("[年で動く表現] 問題編に順位・シェアを問う表現なし OK"
              f"（除外語: {'／'.join(RANK_ALLOW)}）")

    # ============================================================ V7 出典と年次
    for label, tbl in (("表1", P2._T1), ("表2", P2._T2)):
        note = TAG.sub(" ", tbl)
        if not re.search(r"(19|20)[0-9]{2}年|令和[0-9]+年", note):
            g._warn(f"[出典] {label} の注記に統計年次が書かれていない")
    g._ok("[出典] 統計表の注記に年次あり OK")
