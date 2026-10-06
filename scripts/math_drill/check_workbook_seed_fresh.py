#!/usr/bin/env python3
"""📐 seed-data/math_drill_workbook_v1.json が生成元から組み直した結果と同じかを見る鮮度ゲート (run_all_gates.py が拾う)。

生成元: scripts/math_workbook/content_*.py (問題集) → extract_workbook_items.py → data/workbook_choices.json (誤答・注記)
        + build_math_workbook_seed.py の表 (DROP / UNIT_FIX / EXPL_FIX / AV_SHAPE_CHECKED)。
どれかを直したのに builder を回さずに push すると、CEO の補充ボタンは古いシードを入れ続ける (2026-10-06 レビュー)。
問題集の問題文・答えを直したときは builder 自体が止まる (stem_hash / answer_hash) ので、ここでもその問題がそのまま出る。

判定: builder の build() + validate() をメモリ上で回し (ファイルは書かない)、問題 (questions) と本番で止める問題
(_meta.retired_sources) がコミット済みのシードと完全一致すれば PASS。違えば何が違うかを出して exit 1。
直し方: python3 scripts/math_drill/build_math_workbook_seed.py を回してシードもコミットする。
"""
import importlib.util
import io
import contextlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SEED = os.path.join(REPO, "seed-data", "math_drill_workbook_v1.json")


def main():
    spec = importlib.util.spec_from_file_location("build_math_workbook_seed", os.path.join(HERE, "build_math_workbook_seed.py"))
    B = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(B)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        qs = B.build()
        B.validate(qs)
    if B.problems:
        print(f"FAIL: builder の検査で {len(B.problems)} 件 (組み直せない状態)")
        for p in B.problems[:30]:
            print("  -", p)
        return 1
    committed = json.load(open(SEED, encoding="utf-8"))
    cq = committed.get("questions") or []
    diffs = []
    if len(cq) != len(qs):
        diffs.append(f"問題数: コミット済み {len(cq)} / 組み直し {len(qs)}")
    by_src = {q["source"]: q for q in cq}
    for q in qs:
        o = by_src.get(q["source"])
        if o is None:
            diffs.append(f"{q['source']}: コミット済みのシードに無い")
        elif o != q:
            keys = sorted(k for k in set(o) | set(q) if o.get(k) != q.get(k))
            diffs.append(f"{q['source']}: {', '.join(keys)} が違う")
    gone = sorted(set(by_src) - {q["source"] for q in qs})
    if gone:
        diffs.append(f"組み直しに無い問題: {gone[:5]}")
    if [q["source"] for q in cq] != [q["source"] for q in qs] and not diffs:
        diffs.append("問題の並び順が違う")
    if (committed.get("_meta") or {}).get("retired_sources") != B.retired_sources():
        diffs.append("_meta.retired_sources (本番で止める問題) が違う")
    if diffs:
        print(f"FAIL: シードが生成元と食い違う ({len(diffs)} 件)。python3 scripts/math_drill/build_math_workbook_seed.py を回してシードもコミットすること")
        for d in diffs[:30]:
            print("  -", d)
        return 1
    print(f"PASS: math_drill_workbook_v1.json は生成元から組み直した結果と一致 ({len(qs)} 問・止める問題 {len(B.retired_sources())})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
