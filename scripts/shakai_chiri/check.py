# -*- coding: utf-8 -*-
"""
中学社会 地理演習  機械ゲート（build.py が先に実行し、FAIL ならビルドを中止する）

検査するもの（すべて "作った本人の申告" ではなく機械が数え直す）:
  1. 雨温図：月別値が12個か／月別値から再計算した年平均気温・年降水量が出典の年値と一致するか
  2. 雨温図：軸の範囲（-10〜40℃ / 0〜500mm）に全データが収まるか（はみ出すと図が嘘になる）
  3. 判別問題：正解が「その雨温図の実データ」と矛盾しないか（南半球・0℃下回り・年降水量）
  4. 記述：模範解答の字数を数え直して limit 以内か
  5. 選択肢問題：ans がレンジ内か／正解位置が特定の番号に偏っていないか
  6. match：解答が pool の記号と1対1対応か
  7. 一問一答：問題文・解答の重複がないか
  8. 時差：解説の計算を独立に再計算して一致するか
  9. 全問に exp があるか／配点合計が META の総点と一致するか
 10. 文字：PDF フォント(Arial Unicode)に無い絵文字・制御文字が混ざっていないか
"""
import sys, re, json, unicodedata
from collections import Counter

import content_no01 as C

FAIL = []
WARN = []


def fail(msg):
    FAIL.append(msg)


def warn(msg):
    WARN.append(msg)


# ---------------------------------------------------------------- 1,2. 雨温図
def check_charts():
    for label, (name, (temps, precs)) in C.CHART_SRC.items():
        if len(temps) != 12 or len(precs) != 12:
            fail(f"[雨温図] {label}({name}) 月別値が12個でない: 気温{len(temps)} 降水{len(precs)}")
            continue
        exp_t, exp_p = C.EXPECTED[name]
        got_t = round(sum(temps) / 12, 1)
        got_p = round(sum(precs), 1)
        if abs(got_t - exp_t) > 0.3:
            fail(f"[雨温図] {name} 年平均気温が出典と不一致: 月別再計算={got_t} 出典={exp_t}")
        if abs(got_p - exp_p) > 1.0:
            fail(f"[雨温図] {name} 年降水量が出典と不一致: 月別再計算={got_p} 出典={exp_p}")
        # 軸レンジ
        if min(temps) < -10 or max(temps) > 40:
            fail(f"[雨温図] {name} 気温が軸(-10〜40℃)からはみ出す: {min(temps)}〜{max(temps)}")
        if max(precs) > 500:
            fail(f"[雨温図] {name} 降水量が軸(0〜500mm)からはみ出す: max={max(precs)}")
        print(f"  [chart] {label} {name:10s} 年平均{got_t:5.1f}℃ 年降水{got_p:7.1f}mm "
              f"(出典 {exp_t}℃ / {exp_p}mm) OK")


# ---------------------------------------------------------------- 3. 判別問題の実データ整合
POOL_TO_NAME = {
    "大問1": {"ア": "バンコク", "イ": "リヤド", "ウ": "モスクワ", "エ": "ブエノスアイレス"},
    "大問2": {"ア": "高田", "イ": "松本", "ウ": "高松", "エ": "那覇"},
}


def check_match_against_data():
    for b in C.PART2:
        for q in b["qs"]:
            if q["type"] != "match":
                continue
            m = POOL_TO_NAME.get(b["no"])
            if not m:
                continue
            for slot, kana in zip(q["slots"], q["ans"]):
                claimed = m[kana]
                actual = C.CHART_SRC[slot][0]
                if claimed != actual:
                    fail(f"[判別] {b['no']} {slot} の正解が図の実データと不一致: "
                         f"解答={claimed} 実データ={actual}")
                else:
                    print(f"  [match] {b['no']} {slot}={kana} → {actual} OK")

    # 判別根拠そのものを実データで検算する
    t, _ = C.W_BSAS
    if t.index(max(t)) > 5:
        fail("[判別根拠] ブエノスアイレスの最暖月が前半でない＝南半球という解説が成立しない")
    else:
        print(f"  [根拠] ブエノスアイレス 最暖月={t.index(max(t))+1}月 → 南半球 OK")
    t, _ = C.W_MOSCOW
    below = sum(1 for x in t if x < 0)
    if below == 0:
        fail("[判別根拠] モスクワに0℃未満の月が無く、冷帯という解説が成立しない")
    else:
        print(f"  [根拠] モスクワ 0℃未満={below}か月 年較差={max(t)-min(t):.1f}℃ OK")
    t, p = C.W_BANGKOK
    if min(t) < 18:
        fail("[判別根拠] バンコクの最寒月が18℃未満で、熱帯という解説が成立しない")
    else:
        print(f"  [根拠] バンコク 最寒月={min(t)}℃ 乾季(11-2月)計={p[10]+p[11]+p[0]+p[1]:.1f}mm OK")
    _, p = C.W_RIYADH
    if sum(p) > 300:
        fail("[判別根拠] リヤドの年降水量が多すぎて砂漠気候という解説が成立しない")
    # 高田＝冬に降水集中／松本・高松＝少雨／那覇＝高温 を検算
    _, p = C.J_TAKADA
    win, sum_ = p[11] + p[0] + p[1], p[5] + p[6] + p[7]
    if win <= sum_:
        fail(f"[判別根拠] 高田の冬降水({win:.1f})が夏降水({sum_:.1f})を上回っていない")
    else:
        print(f"  [根拠] 高田 冬(12-2月)={win:.1f}mm > 夏(6-8月)={sum_:.1f}mm OK")
    tm, _ = C.J_MATSUMOTO
    tk, _ = C.J_TAKAMATSU
    if not (tm[0] < 0 <= tk[0]):
        fail(f"[判別根拠] 松本と高松を『冬の気温』で区別する解説が成立しない: "
             f"松本1月={tm[0]} 高松1月={tk[0]}")
    else:
        print(f"  [根拠] 松本1月={tm[0]}℃ < 0℃ ≦ 高松1月={tk[0]}℃ で区別可 OK")
    tn, _ = C.J_NAHA
    if min(tn) < 15:
        fail("[判別根拠] 那覇の最寒月が15℃未満で、南西諸島という解説が弱い")
    else:
        print(f"  [根拠] 那覇 最寒月={min(tn)}℃ OK")


# ---------------------------------------------------------------- 4. 記述の字数
def check_desc():
    n = 0
    for src, tag in ((sum([b["qs"] for b in C.PART2], []), "第2部"), (C.PART3, "第3部")):
        for i, q in enumerate(src, start=1):
            if q.get("type") != "desc":
                continue
            n += 1
            ln = len(q["ans"])
            if ln > q["limit"]:
                fail(f"[記述] {tag} 模範解答が字数超過: {ln}字 > 制限{q['limit']}字 「{q['ans']}」")
            elif ln < q["limit"] * 0.5:
                warn(f"[記述] {tag} 模範解答が制限より大幅に短い: {ln}字 / 制限{q['limit']}字")
            else:
                print(f"  [desc] {tag} {ln:2d}字 / 制限{q['limit']}字 OK")
            if not q.get("keys"):
                fail(f"[記述] {tag} 採点のポイント(keys)が無い: 「{q['q'][:24]}…」")
    print(f"  [desc] 記述 合計 {n} 問")


# ---------------------------------------------------------------- 5,6. 選択肢・match
def check_choice():
    pos = Counter()
    total = 0
    for b in C.PART2:
        for i, q in enumerate(b["qs"], start=1):
            if q["type"] == "mc":
                total += 1
                if not (0 <= q["ans"] < len(q["choices"])):
                    fail(f"[選択] {b['no']} 問{i} ans が範囲外: {q['ans']}")
                    continue
                pos[q["ans"]] += 1
                if len(set(q["choices"])) != len(q["choices"]):
                    fail(f"[選択] {b['no']} 問{i} 選択肢に重複がある")
            elif q["type"] == "match":
                kana = [x.split("　")[0] for x in q["pool"]]
                if sorted(q["ans"]) != sorted(kana):
                    fail(f"[match] {b['no']} 問{i} 解答が pool と1対1でない: "
                         f"{q['ans']} vs {kana}")
                if len(set(q["ans"])) != len(q["ans"]):
                    fail(f"[match] {b['no']} 問{i} 同じ記号を2回使っている: {q['ans']}")
    if total:
        top = max(pos.values())
        dist = "／".join(f'{k+1}番:{pos.get(k,0)}' for k in range(4))
        if top > total * 0.5:
            fail(f"[選択] 正解位置が偏っている（{total}問中 最頻{top}問）: {dist}")
        else:
            print(f"  [選択] 4択 {total}問 正解位置分布 {dist} OK")


# ---------------------------------------------------------------- 7. 一問一答の重複
def check_part1():
    qs, ans = [], []
    for g in C.PART1:
        for it in g["items"]:
            qs.append(it["q"])
            ans.append(it["ans"])
            if not it.get("exp"):
                fail(f"[一問一答] 解説が無い: 「{it['q'][:22]}…」")
    for label, arr in (("問題文", qs), ("解答", ans)):
        dup = [k for k, v in Counter(arr).items() if v > 1]
        if dup:
            fail(f"[一問一答] {label}の重複: {dup}")
    print(f"  [一問一答] {len(qs)}問 問題文重複なし／解答重複なし OK")
    return len(qs)


# ---------------------------------------------------------------- 8. 時差の独立再計算
def check_jisa():
    """content の解説を読まず、経度から独立に計算して答えと突き合わせる。"""
    LON = {"東京": 135, "ロンドン": 0, "ニューヨーク": -75, "シドニー": 150}

    def diff(a, b):
        return abs(LON[a] - LON[b]) / 15

    cases = []
    # 問1: 東京とロンドンの時差
    cases.append(("東京とロンドンの時差", f"{int(diff('東京','ロンドン'))}時間", "9時間"))
    # 問2: 東京 1/10 15:00 発 → 12時間飛行 → ロンドン到着時刻
    lon_at_dep = 15 - diff("東京", "ロンドン")          # ロンドンの現地時刻
    arr = lon_at_dep + 12
    cases.append(("ロンドン到着時刻", f"1月10日 {int(arr)}時", "1月10日 18時"))
    # 問3: NY 1/10 08:00 のときの東京
    tokyo = 8 + diff("東京", "ニューヨーク")
    cases.append(("東京の時刻(NY基準)", f"1月10日 {int(tokyo)}時", "1月10日 22時"))
    # 問4: シドニー 1/10 09:00 のときの東京（東京はシドニーより西＝遅れている）
    tokyo2 = 9 - diff("東京", "シドニー")
    cases.append(("東京の時刻(シドニー基準)", f"1月10日 {int(tokyo2)}時", "1月10日 8時"))

    for name, calc, expect in cases:
        if calc != expect:
            fail(f"[時差] {name}: 独立再計算={calc} だが想定={expect}")
        else:
            print(f"  [時差] {name} 独立再計算={calc} OK")

    # content 側の解答文字列と突き合わせる
    b4 = [b for b in C.PART2 if b["no"] == "大問4"][0]
    want = ["9時間", "1月10日 午後6時", "1月10日 午後10時", "1月10日 午前8時"]
    for i, w in enumerate(want):
        if b4["qs"][i]["ans"] != w:
            fail(f"[時差] 大問4 問{i+1} の解答が想定と違う: {b4['qs'][i]['ans']} != {w}")
    # 午前/午後表記と24時間表記の一致（18時=午後6時 / 22時=午後10時 / 8時=午前8時）
    for text, h24 in ((b4["qs"][1]["ans"], int(arr)), (b4["qs"][2]["ans"], int(tokyo)),
                      (b4["qs"][3]["ans"], int(tokyo2))):
        m = re.search(r"午(前|後)(\d+)時", text)
        if not m:
            fail(f"[時差] 午前/午後表記が読み取れない: 「{text}」")
            continue
        h = int(m.group(2)) + (12 if m.group(1) == "後" else 0)
        if h != h24:
            fail(f"[時差] 午前午後表記が24時間表記と不一致: 「{text}」 vs {h24}時")
    print("  [時差] 午前/午後表記と24時間表記の対応 OK")


# ---------------------------------------------------------------- 9. 解説・配点
def check_meta():
    n1 = sum(len(g["items"]) for g in C.PART1)
    p2 = sum(b["point"] for b in C.PART2)
    p3 = len(C.PART3) * 3
    total = n1 * 1 + p2 + p3
    if total != C.META["total"]:
        fail(f"[配点] 合計が META と不一致: 第1部{n1}＋第2部{p2}＋第3部{p3}＝{total} "
             f"だが META['total']={C.META['total']}")
    else:
        print(f"  [配点] 第1部{n1}点＋第2部{p2}点＋第3部{p3}点＝{total}点 OK")
    for b in C.PART2:
        for i, q in enumerate(b["qs"], start=1):
            if not q.get("exp"):
                fail(f"[解説] {b['no']} 問{i} に exp が無い")
            if q["type"] == "calc" and not q.get("work"):
                fail(f"[解説] {b['no']} 問{i} は計算問題だが work（式）が無い")
    for i, q in enumerate(C.PART3, start=1):
        if not q.get("exp") or not q.get("keys"):
            fail(f"[解説] 第3部 記述{i} に exp / keys が無い")


# ---------------------------------------------------------------- 11. 解答の自己漏洩
# 「問題編の別の場所に第1部の答えが印字されている」事故を機械検出する。
# 初版では冒頭のポイント整理に島名・数値・方位を書いたため 40問中15問が知識ゼロで取れた。
# ポイント整理は解答解説編へ移したので、ここでは問題編に載るものだけを走査する。
LEAK_ALLOW = {
    # 解答 : 長い語の一部として現れるだけで、答えの手がかりにならないもの（理由を必ず書く）
    "太平洋": "記述5の「太平洋ベルト」の一部。設問は『三大洋で最大の海洋』なので手がかりにならない",
}


def check_answer_leak():
    printed = " ".join([
        json.dumps([{k: v for k, v in b.items() if k != "figs"} for b in C.PART2], ensure_ascii=False),
        # 表の中身（figs）も問題編に印字されるので必ず含める
        " ".join(str(f) for b in C.PART2 for f in b.get("figs", [])),
        " ".join(q["q"] for q in C.PART3),
    ])
    n, leaks, allowed = 0, [], []
    for g in C.PART1:
        for it in g["items"]:
            n += 1
            a = re.sub(r"^約|（.*?）|\(.*?\)", "", it["ans"]).strip()
            if len(a) < 3 or a not in printed:
                continue
            if a in LEAK_ALLOW:
                allowed.append(f'({n}) {a}')
            else:
                leaks.append(f'({n}) {it["ans"]}')
    if leaks:
        fail(f"[解答漏洩] 第1部{n}問中 {len(leaks)}問の答えが問題編の別の場所に印字されている: "
             + "／".join(leaks))
    else:
        print(f"  [解答漏洩] 第1部{n}問 problem-side への漏洩なし OK"
              + (f"（許容: {'／'.join(allowed)}）" if allowed else ""))


# ---------------------------------------------------------------- 12. 正解肢が最長のテル
def check_longest_tell():
    tot, longest = 0, 0
    detail = []
    for b in C.PART2:
        for i, q in enumerate(b["qs"], start=1):
            if q["type"] != "mc":
                continue
            tot += 1
            L = [len(c) for c in q["choices"]]
            if L[q["ans"]] == max(L):
                longest += 1
                detail.append(f'{b["no"]}問{i}({L[q["ans"]]}字/最長{max(L)})')
    if tot and longest > tot * 0.5:
        fail(f"[テル] 4択{tot}問中 {longest}問で正解肢が最長（期待値{tot/4:.1f}問）。"
             f"長さだけで当てられる: " + "／".join(detail))
    else:
        print(f"  [テル] 4択{tot}問中 正解肢が最長なのは{longest}問（期待値{tot/4:.1f}）OK")


# ---------------------------------------------------------------- 13. 記述の文末が問いに正対しているか
ASK_END = [
    ("利点", ("点。", "こと。", "ができる。", "がある。")),
    ("影響", ("なる。", "る。", "。")),
]


def check_desc_ending():
    REASON = ("理由", "なぜ", "原因", "わけ")   # これらを聞いていれば「〜から。」で正しい
    bad = []

    def scan(q, where):
        asks_reason = any(k in q["q"] for k in REASON)
        if q["ans"].endswith("から。") and not asks_reason:
            bad.append(f'{where}（問い「…{q["q"][-14:]}」／解答「…{q["ans"][-6:]}」）')

    for i, q in enumerate(C.PART3, start=1):
        scan(q, f'記述{i}')
    for b in C.PART2:
        for i, q in enumerate(b["qs"], start=1):
            if q["type"] == "desc":
                scan(q, f'{b["no"]}問{i}')
    if bad:
        fail("[記述] 理由を聞いていないのに模範解答が「〜から。」で終わっている"
             "（公立入試では文末不一致で減点）: " + "／".join(bad))
    else:
        print("  [記述] 設問の問い（理由/利点/問題/影響）と模範解答の文末が一致 OK")


# ---------------------------------------------------------------- 14. 解説の月数主張をデータで検算
def check_exp_month_claim():
    """解説が「N か月が0℃を下回り」と書いたら、実データの月数と照合する。
    初版はモスクワを『1月・2月・11月・12月』＝4か月と書いたが実際は3月も含め5か月だった。"""
    q = C.PART2[0]["qs"][0]
    t, _ = C.W_MOSCOW
    actual = sum(1 for x in t if x < 0)
    m = re.search(r"(\d+)\s*か月が0℃を下回り", q["exp"])
    if not m:
        warn("[解説検算] モスクワの0℃未満月数の主張が解説から読み取れない（書式変更?）")
        return
    if int(m.group(1)) != actual:
        fail(f"[解説検算] モスクワの0℃未満月数: 解説={m.group(1)}か月 実データ={actual}か月")
    else:
        print(f"  [解説検算] モスクワ 0℃未満={actual}か月 と解説が一致 OK")


# ---------------------------------------------------------------- 16. 解説の選択肢番号ズレ
CIRC = "①②③④⑤⑥"


def check_exp_choice_refs():
    """選択肢を並べ替えたのに解説の「①は〜、③は〜」を直し忘れる典型事故を検出する。
    解説が誤答として名指しした番号に正解番号が含まれていたら FAIL。"""
    n = 0
    for b in C.PART2:
        for i, q in enumerate(b["qs"], start=1):
            if q["type"] != "mc":
                continue
            refs = {CIRC.index(c) for c in q["exp"] if c in CIRC}
            if not refs:
                continue
            n += 1
            if q["ans"] in refs:
                fail(f"[解説参照] {b['no']}問{i} 解説が正解{CIRC[q['ans']]}を誤答として説明している"
                     f"（選択肢の並べ替え後に直し忘れ）")
            bad = [r for r in refs if r >= len(q["choices"])]
            if bad:
                fail(f"[解説参照] {b['no']}問{i} 解説が存在しない選択肢を参照: "
                     + "".join(CIRC[r] for r in bad))
            print(f"  [解説参照] {b['no']}問{i} 誤答として言及={''.join(CIRC[r] for r in sorted(refs))} "
                  f"／正解={CIRC[q['ans']]} 衝突なし OK")
    if n == 0:
        print("  [解説参照] 選択肢番号を参照する解説なし")


# ---------------------------------------------------------------- 15. 小問配点
def check_subpoints():
    for b in C.PART2:
        pts = [q.get("pt") for q in b["qs"]]
        if not all(pts):
            fail(f"[配点] {b['no']} に小問配点(pt)が無い設問がある: {pts}")
            continue
        if sum(pts) != b["point"]:
            fail(f"[配点] {b['no']} 小問配点の合計{sum(pts)} != 大問配点{b['point']}")
        else:
            print(f"  [配点] {b['no']} 小問{pts} 合計{sum(pts)} = 大問配点{b['point']} OK")


# ---------------------------------------------------------------- 10. 文字監査
SAFE_EXTRA = set("①②③④⑤⑥―－−℃²³　★●◆▲")


def walk(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for v in o.values():
            yield from walk(v)
    elif isinstance(o, (list, tuple)):
        for v in o:
            yield from walk(v)


def check_glyphs():
    bad = Counter()
    for name in ("META", "POINTS", "PART1", "PART2", "PART3"):
        for s in walk(getattr(C, name)):
            for ch in s:
                if ch in SAFE_EXTRA or ch in "\n\t":
                    continue
                cp = ord(ch)
                if cp < 0x20:
                    bad[f"制御文字 U+{cp:04X}"] += 1
                elif 0x1F000 <= cp <= 0x1FAFF or 0x2600 <= cp <= 0x27BF or cp in (0xFE0F, 0x20E3):
                    bad[f"絵文字 {ch} U+{cp:04X}"] += 1
                elif unicodedata.category(ch) in ("Cn", "Co", "Cs"):
                    bad[f"未定義/私用領域 {ch} U+{cp:04X}"] += 1
    if bad:
        for k, v in bad.items():
            fail(f"[文字] PDF で黒四角/豆腐になる文字: {k} ×{v}")
    else:
        print("  [文字] 絵文字・制御文字・私用領域 なし OK")


# ---------------------------------------------------------------- 実行
def main():
    print("=== 中学社会 地理演習 No.01 機械ゲート ===")
    print("[1-2] 雨温図データ");        check_charts()
    print("[3]   判別問題 vs 実データ"); check_match_against_data()
    print("[4]   記述の字数");          check_desc()
    print("[5-6] 選択肢・match");       check_choice()
    print("[7]   一問一答の重複");       check_part1()
    print("[8]   時差の独立再計算");     check_jisa()
    print("[9]   配点・解説の有無");     check_meta()
    print("[10]  文字監査");            check_glyphs()
    print("[11]  解答の自己漏洩");       check_answer_leak()
    print("[12]  正解肢が最長のテル");   check_longest_tell()
    print("[13]  記述の文末と問いの対応"); check_desc_ending()
    print("[14]  解説の主張をデータで検算"); check_exp_month_claim()
    print("[15]  小問配点");            check_subpoints()
    print("[16]  解説の選択肢番号ズレ"); check_exp_choice_refs()

    print()
    for w in WARN:
        print("WARN:", w)
    if FAIL:
        print(f"\n=== FAIL {len(FAIL)}件 ===")
        for f in FAIL:
            print(" ×", f)
        sys.exit(1)
    print(f"\n=== ALL PASS ({len(WARN)} warnings) ===")


if __name__ == "__main__":
    main()
