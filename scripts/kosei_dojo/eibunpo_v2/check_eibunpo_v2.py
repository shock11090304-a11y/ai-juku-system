#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CI ゲート (読むだけ・書かない・つながない): eibunpo_v2 の verified/ と build/rows.json の整合を検査する。
    python3 scripts/kosei_dojo/eibunpo_v2/check_eibunpo_v2.py
見るもの: 形式 (4択・正解範囲・unit の形・位置語・解説の接頭辞)・既存プール/単元ドリル/内部の重複・カードの一致・
         正解位置の均等・bank の LIKE 予算・build/rows.json が verified と同じ設問集合で、選択肢の並び・正解・解説・設問文まで一致するか。
verified/ が空 (まだ作問前) のときは何もせず PASS。
"""
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib as L  # noqa: E402
import build as B  # noqa: E402  (関数だけ使う。main は呼ばない)

VD = os.path.join(L.HERE, "verified"); OUT = os.path.join(L.HERE, "build")


def main():
    units, qs = B.load_verified()
    if not qs:
        print("eibunpo_v2: verified/ が空 (作問前) → PASS"); return 0
    errs, warns = B.gates(units, qs)
    rp = os.path.join(OUT, "rows.json")
    if os.path.exists(rp):
        rows = json.load(open(rp, encoding="utf-8"))
        cards = {(u["part"], u["filter"]): u for u in units}
        v_sigs = collections.Counter(L.sig(q["stem"], q["choices"]) for q in qs)
        r_sigs = collections.Counter()
        v_by = {L.sig(q["stem"], q["choices"]): q for q in qs}
        for r in rows:
            part = r.get("part_key"); qd = r.get("question_data") or {}
            if part not in L.PARTS: errs.append(("rows.json", f"part_key が不正: {part!r}")); continue
            if qd.get("source") != L.SOURCE: errs.append(("rows.json", f"source が {qd.get('source')!r}"))
            if qd.get("subject") != L.SUBJECT: errs.append(("rows.json", f"subject が {qd.get('subject')!r}"))
            if str(qd.get("passage") or ""): errs.append(("rows.json", "英文法の行に本文がある"))
            qq = qd.get("questions") or []
            ids = [q.get("id") for q in qq]
            if len(set(ids)) != len(ids): errs.append(("rows.json", f"同じ行の中で問題 id が重複: {ids}"))
            if not (1 <= len(qq) <= L.CHUNK): errs.append(("rows.json", f"行の小問数が {len(qq)} (1〜{L.CHUNK} でない)"))
            filters = set()
            for q in qq:
                where = f"{q.get('stem', '')[:30]!r}"
                r_sigs[L.sig(q.get("stem"), q.get("choices"))] += 1
                a = q.get("answer")
                if not isinstance(a, int) or not (0 <= a < 4):
                    errs.append(("rows.json", f"answer が 0〜3 の整数でない: {a!r}: {where}")); continue
                if q.get("type") != "multiple_choice": errs.append(("rows.json", f"type が multiple_choice でない: {where}"))
                up = L.unit_parts(q.get("unit"))
                card = next((c for (p, f), c in cards.items() if p == part and up and up[0] == c["tag"]), None)
                if not card: errs.append(("rows.json", f"unit がどのカードの tag でもない: {q.get('unit')!r}: {where}")); continue
                filters.add(card["filter"])
                if not str(q.get("explanation", "")).startswith(L.expl_head(q["unit"], q["choices"][a])):
                    errs.append(("rows.json", f"解説の接頭辞が正解と不一致: {where}"))
                vq = v_by.get(L.sig(q.get("stem"), q.get("choices")))
                if not vq: continue
                if vq["answer_index"] != a: errs.append(("rows.json", f"正解位置が verified と違う: {where}"))
                if vq["choices"] != q.get("choices"): errs.append(("rows.json", f"選択肢の並びが verified と違う: {where}"))
                if vq["stem"] != q.get("stem"): errs.append(("rows.json", f"設問文が verified と一字一句一致しない: {where}"))
                if vq["explanation"] != q.get("explanation"): errs.append(("rows.json", f"解説が verified と違う → build.py を回し直す: {where}"))
                if vq["unit"] != q.get("unit"): errs.append(("rows.json", f"unit が verified と違う: {where}"))
                if vq["_part"] != part: errs.append(("rows.json", f"part_key が verified と違う ({part} / {vq['_part']}): {where}"))
            if len(filters) > 1: errs.append(("rows.json", f"1 行に複数カードの小問が混在: {sorted(filters)}"))
        if v_sigs != r_sigs:
            only_v = sum((v_sigs - r_sigs).values()); only_r = sum((r_sigs - v_sigs).values())
            errs.append(("rows.json", f"verified と設問集合が違う (verified のみ {only_v} / rows のみ {only_r}) → build.py を回し直す"))
    else:
        warns.append(("build", "build/rows.json が無い (まだ build.py 前)"))
    per_part = collections.Counter(q["_part"] for q in qs)
    print(f"eibunpo_v2: 設問 {len(qs)} (" + " ".join(f"{p}={per_part[p]}" for p in L.PARTS if per_part[p]) + f") / warn {len(warns)}")
    for w in warns[:40]: print("  warn", w[0], w[1][:110])
    if errs:
        print(f"[GATE] NG {len(errs)} 件")
        for e in errs[:80]: print("  NG:", e[0], e[1][:140])
        return 1
    print("PASS eibunpo_v2 (NG 0 件)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
