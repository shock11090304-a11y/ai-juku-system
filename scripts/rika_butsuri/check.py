# -*- coding: utf-8 -*-
"""
中学理科［物理分野］確認プリント 機械ゲート。

  python3 check.py     → ALL PASS なら exit 0、FAIL があれば exit 1

構成:
  ・教科非依存の 9 ゲート …… scripts/_workbook_check.py（配点／選択肢／解答漏洩／テル／字数…）
  ・物理固有の数値検算  …… verify.py の extra()（オームの法則・仕事とエネルギー・圧力・力の合成を
                            content の定数から**独立に再計算**して、手打ちの答えと照合する）
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))          # scripts/ を import path に

from _workbook_check import run_generic             # noqa: E402
import content_no01 as C                            # noqa: E402

LEAK_ALLOW = getattr(C, "LEAK_ALLOW", {})


def main():
    print("=== 中学理科［物理分野］確認プリント check ===")
    g = run_generic(C, leak_allow=LEAK_ALLOW)
    # ★try/except ImportError で囲うと、**verify.py の中で起きた ImportError まで飲み込む**
    #   （定数のリネーム、依存の欠落、タイポ）。実験で確認: verify.py を壊すと
    #   「verify.py が無い」と嘘の警告を出したうえで ALL PASS / exit 0 になり、
    #   教科固有の数値検算がゼロのまま build がPDFを書いてしまう。
    #   → ファイルの有無だけを os.path.exists で見て、あるなら囲わずに import する。
    if not os.path.exists(os.path.join(HERE, "verify.py")):
        g._warn("verify.py が無い（物理固有の数値検算がスキップされている）")
    else:
        import verify
        verify.extra(C, g)
    g.report()


if __name__ == "__main__":
    main()
