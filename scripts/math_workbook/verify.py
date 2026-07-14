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

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else None
    mods = [f"content_{which}"] if which else ["content_ia", "content_iib"]
    total_fail = total_dup = 0
    for m in mods:
        try:
            f, d = run(m)
            total_fail += f; total_dup += d
        except ModuleNotFoundError:
            print(f"(skip {m}: not found)")
    print(f"\n==== TOTAL FAIL={total_fail}  DUP={total_dup} ====")
    sys.exit(1 if (total_fail or total_dup) else 0)
