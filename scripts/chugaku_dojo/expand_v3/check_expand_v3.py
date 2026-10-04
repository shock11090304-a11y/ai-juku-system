#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CI ゲート (読むだけ・書かない・つながない): expand_v3 の verified/ と build/rows.json の整合を検査する。
    python3 scripts/chugaku_dojo/expand_v3/check_expand_v3.py
見るもの: 形式 (4択・正解範囲・位置語なし・解説の接頭辞)・既存プール/内部の重複・単元名の一致・
         正解位置の均等・bank の LIKE 予算 (単元名を含む行が画面の取得行数 = 読解 32 / それ以外 50 を超えない)・
         build/rows.json が verified と同じ設問集合で、選択肢の並び・正解・解説・本文まで一致するか。
verified/ が空 (まだ作問前) のときは何もせず PASS。
"""
import collections
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _v3lib as L  # noqa: E402
import build as B  # noqa: E402  (関数だけ使う。main は呼ばない)

VD = os.path.join(L.HERE, "verified"); OUT = os.path.join(L.HERE, "build")


def main():
    units, qs = B.load_verified()
    if not qs:
        print("expand_v3: verified/ が空 (作問前) → PASS"); return 0
    errs, warns = B.gates(units, qs)
    # build/rows.json との整合
    rp = os.path.join(OUT, "rows.json")
    if os.path.exists(rp):
        rows = json.load(open(rp, encoding="utf-8"))
        v_sigs = collections.Counter(L.sig(q["stem"], q["choices"]) for q in qs)
        r_sigs = collections.Counter()
        for r in rows:
            if r.get("source") != L.SOURCE: errs.append(("rows.json", f"source が {r.get('source')!r}"))
            for q in r.get("questions", []):
                r_sigs[L.sig(q["stem"], q["choices"])] += 1
                try: a = int(q["answer"])
                except Exception: errs.append(("rows.json", f"answer が整数文字列でない: {q.get('answer')!r}")); continue
                if not (0 <= a < 4): errs.append(("rows.json", f"answer 範囲外: {a}"))
                elif not q["explanation"].startswith(L.expl_head(r["format_type"], q["choices"][a])):
                    errs.append(("rows.json", f"解説の接頭辞が正解と不一致: {q['stem'][:30]!r}"))
                if q.get("unit") != r.get("format_type"): errs.append(("rows.json", f"unit != format_type: {q['stem'][:30]!r}"))
        if v_sigs != r_sigs:
            only_v = sum((v_sigs - r_sigs).values()); only_r = sum((r_sigs - v_sigs).values())
            errs.append(("rows.json", f"verified と設問集合が違う (verified のみ {only_v} / rows のみ {only_r}) → build.py を回し直す"))
        # 中身の照合: 正解位置・選択肢の並び・解説・本文が verified と完全一致するか
        #   (verified の解説を直して build.py を回し忘れると、本番に入る rows.json が古いままになるのを止める)
        v_by = {L.sig(q["stem"], q["choices"]): q for q in qs}
        for r in rows:
            ids = [q.get("id") for q in r["questions"]]
            if len(set(ids)) != len(ids): errs.append(("rows.json", f"同じ行の中で問題 id が重複: {ids}"))
            for q in r["questions"]:
                vq = v_by.get(L.sig(q["stem"], q["choices"]))
                if not vq: continue
                where = f"{q['stem'][:30]!r}"
                if r.get("subject") != B.SUBJ[vq["_part"]]:   # insert.py はこの値で part_key を決める
                    errs.append(("rows.json", f"subject が {r.get('subject')!r} (verified は {B.SUBJ[vq['_part']]}): {where}"))
                if vq["stem"] != q["stem"]: errs.append(("rows.json", f"設問文が verified と一字一句一致しない (空白・改行): {where}"))
                try: a = int(q["answer"])
                except Exception: continue   # 上のループで NG 済み
                if vq["answer_index"] != a: errs.append(("rows.json", f"正解位置が verified と違う: {where}"))
                if vq["choices"] != q["choices"]: errs.append(("rows.json", f"選択肢の並びが verified と違う: {where}"))
                if vq["explanation"] != q["explanation"]: errs.append(("rows.json", f"解説が verified と違う → build.py を回し直す: {where}"))
                if str(vq.get("passage") or "") != str(r.get("passage") or ""): errs.append(("rows.json", f"本文が verified と違う: {where}"))
    else:
        warns.append(("build", "build/rows.json が無い (まだ build.py 前)"))
    per_part = collections.Counter(q["_part"] for q in qs)
    print(f"expand_v3: 設問 {len(qs)} (" + " ".join(f"{p}={per_part[p]}" for p in L.PARTS if per_part[p]) + f") / warn {len(warns)}")
    for w in warns[:40]: print("  warn", w[0], w[1][:110])
    if errs:
        print(f"[GATE] NG {len(errs)} 件")
        for e in errs[:80]: print("  NG:", e[0], e[1][:140])
        return 1
    print("PASS expand_v3 (NG 0 件)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
