#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""content_ia / content_iib の全問について、各問に埋めた chk() を実行し
sympy で答えを独立再計算 → 一致を確認する。失敗・未検証を列挙する。

  python3 verify.py ia
  python3 verify.py iib
  python3 verify.py         # 両方
"""
import sys, importlib, traceback

def run(modname):
    mod = importlib.import_module(modname)
    units = mod.UNITS
    ok = fail = manual = 0
    fails = []
    manuals = []
    seen_stems = {}
    dups = []
    for u in units:
        for j, q in enumerate(u["problems"], 1):
            tag = f'{modname}:{u["name"]}#{j}'
            stem = q.get("stem", "").strip()
            if stem in seen_stems:
                dups.append((tag, seen_stems[stem]))
            else:
                seen_stems[stem] = tag
            chk = q.get("chk")
            if chk is None:
                manual += 1
                manuals.append(f'{tag}  {stem[:48]}')
                continue
            try:
                res = chk()
                if res is True:
                    ok += 1
                else:
                    fail += 1
                    fails.append(f'{tag}  chk returned {res!r}  | stem: {stem[:60]}')
            except Exception as e:
                fail += 1
                fails.append(f'{tag}  EXC {type(e).__name__}: {e}  | stem: {stem[:60]}')
    print(f"\n===== {modname} =====")
    print(f"units={len(units)}  problems={ok+fail+manual}  OK={ok}  FAIL={fail}  manual(no-chk)={manual}")
    if dups:
        print(f"\n-- DUPLICATE stems ({len(dups)}) --")
        for a, b in dups:
            print(f"  DUP {a}  ==  {b}")
    if fails:
        print(f"\n-- FAILURES ({len(fails)}) --")
        for f in fails:
            print("  ✗", f)
    if manuals:
        print(f"\n-- MANUAL review needed (no chk) ({len(manuals)}) --")
        for m in manuals:
            print("  ?", m)
    return fail, len(dups)

ALIAS = {"ia2": "content_ia_v2", "iib2": "content_iib_v2",
         "ia": "content_ia", "iib": "content_iib"}
if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else None
    if which:
        mods = [ALIAS.get(which, f"content_{which}")]
    else:
        # ★引数なしのときは **刷る本を全部** 検査する。以前は ia/iib だけで、
        #   build_html.py が実際に刷る content_ia_v2 / content_iib_v2 が対象外だった
        #   （run_all_gates.py は引数を渡さないので、CI の緑が旧版しか見ていなかった）。
        #   kiso / kiso2 も UNITS + chk() の同じ規約なのでここで見る
        #   （av 方式の kisoA/I/II/III は verify_kisoA.py の担当。どちらにも属さない本を作らない）。
        mods = ["content_ia", "content_iib", "content_ia_v2", "content_iib_v2",
                "content_kiso", "content_kiso2"]
    total_fail = total_dup = 0
    checked = 0
    for m in mods:
        try:
            f, d = run(m)
            total_fail += f; total_dup += d
            checked += 1
        except ModuleNotFoundError:
            # ★以前はここで黙って skip して exit 0 だった。モジュールを改名しただけで
            #   「1問も検証していないのに ALL PASS」になる（＝検査したつもり）。違反として数える。
            total_fail += 1
            print(f"  × {m} が見つからない（改名したなら verify.py の mods を直すこと）")
    print(f"\n==== TOTAL FAIL={total_fail}  DUP={total_dup}  検査した本={checked}/{len(mods)} ====")
    if checked == 0:
        print("  × 1冊も検査できていない")
        sys.exit(1)
    sys.exit(1 if (total_fail or total_dup) else 0)
