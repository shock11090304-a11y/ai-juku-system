# -*- coding: utf-8 -*-
"""
中学社会 地理演習 No.02 機械ゲート。

  python3 check_no02.py     → ALL PASS なら exit 0、FAIL があれば exit 1

★No.01 の check.py を流用しないこと。あちらは No.01 の雨温図の月別値を定数として
  検算しているので、No.02 に当てても「何も検査していないのに PASS」になる。

構成:
  ・教科非依存の 9 ゲート …… scripts/_workbook_check.py
  ・地理固有の検算       …… verify_no02.py の extra()
      統計表の合計・割合の再計算／時差の独立再計算／雨温図の月別値からの年値再計算／
      「順位・シェアなど年で動く数字を出題していないか」の走査
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))          # scripts/ を import path に

from _workbook_check import run_generic             # noqa: E402
import content_no02 as C                            # noqa: E402

LEAK_ALLOW = getattr(C, "LEAK_ALLOW", {})


def main():
    print("=== 中学社会 地理演習 No.02 check ===")
    g = run_generic(C, leak_allow=LEAK_ALLOW)
    # ★try/except ImportError で囲うと、**verify_no02.py の中で起きた ImportError まで飲み込む**
    #   （定数のリネーム、依存の欠落、タイポ）。実験で確認: verify_no02.py を壊すと
    #   「verify_no02.py が無い」と嘘の警告を出したうえで ALL PASS / exit 0 になり、
    #   教科固有の数値検算がゼロのまま build がPDFを書いてしまう。
    #   → ファイルの有無だけを os.path.exists で見て、あるなら囲わずに import する。
    if not os.path.exists(os.path.join(HERE, "verify_no02.py")):
        g._warn("verify_no02.py が無い（地理固有の検算がスキップされている）")
    else:
        import verify_no02
        verify_no02.extra(C, g)
    g.report()


if __name__ == "__main__":
    main()
