#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A12 直方体の図のラベル検査(_fig_box_clearances)の**自己テスト**。

    python3 check_fig_a12.py

★なぜ要るか
  「今の図で違反 0 件」は、検査がちゃんと見ている証拠にならない。
  何も見ていない検査も同じ 0 件を返す。実際 A12 の docstring には
  「_fig_box_clearances() が見張る」と書いてあったのに、その関数は存在しなかった。
  そこで**わざと壊した図**を渡して、必ず落ちることを確かめる。
  閾値(_MIN_CLEAR_PT / _OWNER_MARGIN_PT)を将来ゆるめると、ここが赤くなる。

★元の不具合(2026-08-07 塾長指摘)
  p20 の直方体だけラベルが 6.3pt(同ページの四角形の図は 10.9pt・本文 9.5pt)で、
  「2」が破線 A-B と灰色の対角線 A-G に重なっていた。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from parts_ia_jaku import A12                                    # noqa: E402

FAIL = 0


def case(name, mutate, expect):
    """mutate で壊した図を検査させ、expect を含む違反が出ることを確かめる。"""
    global FAIL
    orig = A12._box_geometry
    A12._box_geometry = lambda: mutate(*orig())
    try:
        errs = A12._fig_box_clearances()
    except Exception as e:                                        # 検査自体の故障も失敗
        A12._box_geometry = orig
        FAIL += 1
        print(f"  NG  {name}: 検査が例外 {type(e).__name__}: {e}")
        return
    A12._box_geometry = orig
    hit = any(expect in e for e in errs)
    if not hit:
        FAIL += 1
    # ★「検出 N 件」と書く。ここで出る N 件は**壊した図を捕まえた証拠＝合格の姿**で、
    #   このゲート自身の違反ではない。"違反 N 件" と印字すると run_all_gates.py が
    #   「合格を自称しながら違反を印字している」= INCONSISTENT として落とす(実測)。
    print(f"  {'OK ' if hit else 'NG '} {name}: 検出 {len(errs)} 件"
          + ("" if hit else f"  ← 『{expect}』を検出できていない"))
    for e in errs:
        print("         └", e)


def _move(labels, target, dx, dy):
    g = A12._BOX_G
    return [(s, a, dx/g, dy/g, e) if s == target else (s, a, ox, oy, e)
            for s, a, ox, oy, e in labels]


def main():
    global FAIL
    print("=== A12 直方体の図: 壊した図で検査が落ちるか ===")

    # 1. 『2』を旧位置へ。三角形 ABD の中で赤い BD と等距離になり、
    #    『2』が BD(=√13、stem に無い値)のラベルに見えうる配置。
    case("『2』を旧位置(8.5,5.5)へ", lambda c, V, s, L: (c, V, s, _move(L, "2", 8.5, 5.5)),
         "『2』")
    # 2. 『2』を破線 AB の真上に重ねる
    case("『2』を AB の線上へ", lambda c, V, s, L: (c, V, s, _move(L, "2", 0, 0)),
         "接近")
    # 3. 『B』を頂点の左下へ = 灰色の対角線 AG に串刺しにされる旧配置
    case("『B』を頂点の左下へ", lambda c, V, s, L: (c, V, s, _move(L, "B", -13, 13)),
         "接近")
    # 4. 高さを 0.55 倍に潰す(かつての事故。AE が AD の2倍に見えなくなる)
    case("高さを 0.55 倍に潰す",
         lambda c, V, s, L: (c, {n: (x, y*0.55) for n, (x, y) in V.items()}, s, L),
         "倍。")
    # 5. stem に無い数値を書く
    case("stem に無い数値『7』を足す",
         lambda c, V, s, L: (c, V, s, L + [("7", V["H"], 20, 0, None)]),
         "stem に無い数値")
    # 6. ラベル同士を重ねる
    case("『C』を『G』に重ねる",
         lambda c, V, s, L: (c, V, s, [(t, V["G"], 5/A12._BOX_G, 2/A12._BOX_G, e)
                                       if t == "C" else (t, a, dx, dy, e)
                                       for t, a, dx, dy, e in L]),
         "重なっている")

    # 7. 字だけ小さくする(元の不具合そのもの)。_BOX_FS を直接動かす。
    fs = A12._BOX_FS
    A12._BOX_FS = round(fs * 6.3 / 10.83, 3)
    try:
        errs = A12._fig_box_clearances()
    finally:
        A12._BOX_FS = fs
    hit = any("四角形の図は" in e for e in errs)
    if not hit:
        FAIL += 1
    print(f"  {'OK ' if hit else 'NG '} ラベルを 6.3pt に縮める: 検出 {len(errs)} 件")
    for e in errs:
        print("         └", e)

    print("\n=== 今の図(無改変) ===")
    errs = A12._fig_box_clearances(report=True)
    if errs:
        FAIL += len(errs)
        for e in errs:
            print("  ✗", e)
    else:
        print("  問題なし")

    print(f"\n===== 自己テストの失敗 {FAIL} 件 =====")
    if FAIL:
        print("NG — 検査がザルになっているか、図が壊れている")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
