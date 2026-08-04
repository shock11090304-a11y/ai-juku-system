# -*- coding: utf-8 -*-
"""
問題集(第1部 一問一答／第2部 大問／第3部 記述)の**教科非依存**な機械ゲート。

  import sys, os; sys.path.insert(0, <scriptsディレクトリ>)
  from _workbook_check import run_generic
  ok = run_generic(C)          # C = content モジュール（META/POINTS/PART1/PART2/PART3 を持つ）

教科固有の数値検算（オームの法則・質量比・時差など）は各 check.py 側で足すこと。
ここが見るのは「どの教科でも必ず壊れる場所」だけ:

  S1  配点：小問 pt の合計＝大問 point ／ 第1部+第2部+第3部 の合計＝META["total"]
  S2  mc：ans が選択肢のレンジ内か／選択肢が3つ以上あるか／選択肢の重複
  S3  全設問に exp（解説）があるか。calc には work（式）があるか
  S4  第1部：設問文の重複・解答の重複（同じことを2回聞いていないか）
  S5  desc：limit があるか／keys があるか
  S6  calc：ans の単位が unit と一致しているか（「答 ___ Ω」の欄に "0.12A" を入れる事故）
  S7  ★解答漏洩：第1部の答えが**問題編に印字される他の全テキスト**に出ていないか
      （_workbook_gates.Gate.answer_leak。printed_text は本モジュールが組み立てる）
  S8  正解肢が最長のテル／正解位置の偏り／解説の①②③④参照ズレ／記述の文末／採点キー整合／文字
  S9  ★第2部・第3部の答えが問題編の他の場所に印字されていないか（第1部と同じ穴が大問側にも開く）
"""
import os
import re
import sys
import unicodedata
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _workbook_gates import Gate  # noqa: E402

TAG = re.compile(r"<[^>]+>")


def _strip(html_str):
    """inline SVG / table の HTML から、生徒の目に入る文字だけを取り出す。"""
    return TAG.sub(" ", str(html_str))


def all_questions(C):
    """(where, q) の並び。第2部の小問は大問番号つき。"""
    out = []
    for b in C.PART2:
        for i, q in enumerate(b["qs"], start=1):
            out.append((f'{b["no"]}問{i}', q))
    for i, q in enumerate(C.PART3, start=1):
        out.append((f"記述{i}", q))
    return out


def printed_text(C):
    """★問題編に印字される全テキスト。ここに答えが混ざっていれば知識ゼロで得点できる。

    含めるもの：META の説明文、第1部の設問文、第2部の intro/図表/設問文/選択肢、第3部の設問文。
    含めないもの：ans / work / exp / keys / POINTS（すべて解答解説編にしか出ない）。
    """
    buf = [str(C.META.get(k, "")) for k in
           ("title", "subtitle", "intro", "part1_lead", "part2_lead", "part3_lead", "stat_note")]
    for g in C.PART1:
        buf.append(g["group"])
        buf += [it["q"] for it in g["items"]]
    for b in C.PART2:
        buf += [b["no"], b["title"], b.get("intro", "")]
        for f in b.get("figs", []):
            buf.append(_strip(f))
        for q in b["qs"]:
            buf.append(q["q"])
            buf += list(q.get("choices", []))
            buf += list(q.get("pool", [])) + list(q.get("slots", []))
    for q in C.PART3:
        buf.append(q["q"])
        buf += list(q.get("choices", []))
    return " ".join(buf)


def _num_unit(s):
    """'0.12A' -> ('0.12', 'A') / '4：1' -> ('4：1', '')"""
    m = re.match(r"^[約]?([0-9０-９.．/／:：〜~,、\-−+±]+)\s*(.*)$", str(s).strip())
    return (m.group(1), m.group(2).strip()) if m else (str(s), "")


def run_generic(C, leak_allow=None, min_len=2, extra_leak_texts=None, skip=()):
    g = Gate()
    P1 = [it for grp in C.PART1 for it in grp["items"]]
    QS = all_questions(C)
    ptxt = printed_text(C)

    # ---------------------------------------------------------------- S1 配点
    if "pt" not in skip:
        tot2 = 0
        for b in C.PART2:
            s = sum(q.get("pt", 0) for q in b["qs"])
            if s != b["point"]:
                g._fail(f'[配点] {b["no"]} 小問の合計{s}点 ≠ 大問の配点{b["point"]}点')
            tot2 += b["point"]
        p3 = sum(q.get("pt", 3) for q in C.PART3)
        grand = len(P1) * C.META.get("p1_each", 1) + tot2 + p3
        if grand != C.META["total"]:
            g._fail(f'[配点] 第1部{len(P1)}点＋第2部{tot2}点＋第3部{p3}点 ＝ {grand}点 '
                    f'≠ 満点{C.META["total"]}点')
        else:
            g._ok(f"[配点] 第1部{len(P1)}／第2部{tot2}／第3部{p3} ＝ {grand}点 OK")

    # ---------------------------------------------------------------- S2 mc
    mcs = []
    for where, q in QS:
        if q["type"] != "mc":
            continue
        ch = q["choices"]
        if len(ch) < 3:
            g._fail(f"[選択肢] {where} 選択肢が{len(ch)}個しかない")
        if len(set(ch)) != len(ch):
            g._fail(f"[選択肢] {where} 同じ選択肢が2つある")
        if not isinstance(q["ans"], int) or not (0 <= q["ans"] < len(ch)):
            g._fail(f'[選択肢] {where} ans={q["ans"]} が選択肢のレンジ外'
                    "（★ans は 0 始まりの index）")
        mcs.append({"where": where, "choices": ch, "ans": q["ans"], "exp": q.get("exp", "")})
    g._ok(f"[選択肢] 4択{len(mcs)}問 index・重複 OK")

    # ---------------------------------------------------------------- S3 解説/式
    miss = [w for w, q in QS if not str(q.get("exp", "")).strip()]
    miss += [f"({i})" for i, it in enumerate(P1, 1) if not str(it.get("exp", "")).strip()]
    if miss:
        g._fail(f"[解説] 解説が空の設問 {len(miss)}件: " + "／".join(miss[:12]))
    else:
        g._ok(f"[解説] 全{len(QS)+len(P1)}問に解説あり OK")
    nowork = [w for w, q in QS if q["type"] == "calc" and not str(q.get("work", "")).strip()]
    if nowork:
        g._fail("[途中式] calc なのに work が無い: " + "／".join(nowork))
    else:
        g._ok("[途中式] calc は全問 work あり OK")

    # ---------------------------------------------------------------- S4 重複
    for label, vals in (("設問文", [it["q"] for it in P1]), ("解答", [str(it["ans"]) for it in P1])):
        dup = [k for k, v in Counter(vals).items() if v > 1]
        if dup:
            g._fail(f"[第1部重複] 同じ{label}が2回以上: " + "／".join(dup[:8]))
    g._ok(f"[第1部重複] {len(P1)}問 設問文・解答とも重複なし OK")

    # ---------------------------------------------------------------- S5/S6
    descs = []
    for where, q in QS:
        if q["type"] == "desc":
            if not q.get("limit"):
                g._fail(f"[記述] {where} に limit（字数制限）が無い")
            if not q.get("keys"):
                g._fail(f"[記述] {where} に keys（採点のポイント）が無い")
            descs.append({"where": where, "q": q["q"], "ans": q["ans"],
                          "limit": q.get("limit", 40), "keys": q.get("keys", [])})
        elif q["type"] == "calc":
            _, u = _num_unit(q["ans"])
            want = str(q.get("unit", "")).strip()
            if want and u and u != want:
                g._fail(f'[単位] {where} 解答欄の単位「{want}」と模範解答「{q["ans"]}」が食い違う')
            if want and not u:
                g._fail(f'[単位] {where} 解答「{q["ans"]}」に単位が無いのに解答欄には「{want}」')
    g._ok(f"[記述] {len(descs)}問 limit・keys あり／[単位] calc の単位一致 OK")

    # ---------------------------------------------------------------- S7 漏洩（第1部）
    g.answer_leak([{"q": it["q"], "ans": it["ans"]} for it in P1], ptxt,
                  allow=leak_allow or {}, min_len=min_len, extra_texts=extra_leak_texts)

    # ---------------------------------------------------------------- S8 共通ゲート
    g.longest_tell(mcs)
    g.choice_position(mcs)
    g.exp_choice_refs(mcs)
    g.desc_ending(descs)
    g.char_limit(descs)
    g.keys_consistency(descs)
    g.glyphs([C.META, C.POINTS, C.PART1, C.PART2, C.PART3])

    # ---------------------------------------------------------------- S9 漏洩（第2部・第3部）
    # 大問の calc の答えが、別の設問文や図表に印字されていないか（数値は短いので4字以上に限る）
    leaks = []
    for where, q in QS:
        if q["type"] != "calc":
            continue
        a = str(q["ans"]).strip()
        if len(a) < 4:
            continue
        hay = ptxt.replace(q["q"], " ")
        if a in hay:
            leaks.append(f"{where}「{a}」")
    if leaks:
        g._fail("[解答漏洩2] 大問の計算結果が問題編の別の場所に印字されている: " + "／".join(leaks))
    else:
        g._ok("[解答漏洩2] 大問の計算結果 漏洩なし OK")

    return g
