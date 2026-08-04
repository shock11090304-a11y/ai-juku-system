#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""作問パートモジュールの単体ビルド検証。

usage:
  python3 check_part.py ../content/math1a_a.py            # 横書き(数学/英語)
  python3 check_part.py ../content/kokugo_b.py --vertical # 縦書き(国語 問題部)

パートモジュールは SECTIONS(list) と ANS_SECTIONS(list) を定義していること。
検証内容: import可能 / 全ブロックがレンダリング可能 / ChromeでPDF化成功。
出力はスクラッチ(_check_<name>.pdf)。成功なら 'CHECK OK pages=N' を表示。
"""
import importlib.util, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def load_mod(path):
    spec = importlib.util.spec_from_file_location("part_mod", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    path = os.path.abspath(sys.argv[1])
    vertical = "--vertical" in sys.argv
    name = os.path.splitext(os.path.basename(path))[0]
    mod = load_mod(path)
    sections = mod.SECTIONS
    ans_sections = getattr(mod, "ANS_SECTIONS", [])
    meta = {"title": f"check:{name}", "outname": f"_check_{name}", "time": "70分",
            "max_points": 100, "notes": ["チェック用"]}

    if vertical:
        from build_kokugo import build_from
        prob = {"meta": meta, "sections": sections}
        out = os.path.join(HERE, f"_check_{name}.pdf")
        build_from(prob, out, html_name=f"_check_{name}.html")
    else:
        import build_exam
        from common import wrap_doc, chrome_pdf
        prob = {"meta": meta, "sections": sections}
        ans = {"sections": ans_sections}
        body = build_exam.build_problem(prob)
        if ans_sections:
            body += build_exam.build_answer(prob, ans)
        doc = wrap_doc(f"check {name}", f'<div class="eng">{body}</div>' if "english" in name else body,
                       build_exam.EXTRA_CSS + build_exam.ANS_CSS)
        hp = os.path.join(HERE, f"_check_{name}.html")
        with open(hp, "w") as f:
            f.write(doc)
        out = os.path.join(HERE, f"_check_{name}.pdf")
        chrome_pdf(hp, out)

    import fitz
    d = fitz.open(out)
    n = len(d)
    # グリフ監査: 置換文字/NULが無いか
    bad = 0
    for pg in d:
        t = pg.get_text()
        bad += t.count("�") + sum(1 for c in t if ord(c) < 9 and c not in "\n\t")
    d.close()
    print(f"CHECK OK pages={n} bad_glyphs={bad}")
    if bad:
        sys.exit(1)


if __name__ == "__main__":
    main()
