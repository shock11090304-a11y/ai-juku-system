#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生徒の画面で読みにくい表記だけを機械的にそろえる (意味・正解は変えない)。R3 レビューの note から採ったもの。
    python3 scripts/chugaku_dojo/expand_v3/polish_display.py [--apply]
  1. 英語の並べかえで語群が文頭に来る問題に「(文頭に来る語も小文字で示しています。)」(既存プールと同じ文言) を足す
  2. 英語の 2 文書きかえで 2 文目の頭に「= 」が無いものに足す (同じ単元のほかの問題とそろえる)
  3. 数学の引き算の記号 − (U+2212) を、既存プールと同じ半角 - にそろえる (同じ問題の中で混在していた)
  4. 国語 詩歌の詩の字あけを半角スペースから全角スペースにする (スマホでは半角の字あけがほぼ見えない)
  5. 社会 元寇の問題で「」の入れ子になる「てつはう」を『てつはう』にする
変更のたびに: 正解の本文が選択肢に残る・選択肢 4 つが相異なる・(stem, 選択肢) が他と重複しない を assert で確かめる。
既定は何が変わるかを表示するだけ。--apply で verified/ に書き戻す (解説の先頭「正解は「…」」は build.py が組み直す)。
"""
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _v3lib as L  # noqa: E402

VD = os.path.join(L.HERE, "verified")
APPLY = "--apply" in sys.argv
NOTE = "(文頭に来る語も小文字で示しています。)"
JP = r"ぁ-んァ-ヶ一-龥ー々"
POEM_SP = re.compile(rf"(?<=[{JP}、。」])\x20(?=[{JP}「])")


def fix(q, fname):
    before = json.dumps(q, ensure_ascii=False, sort_keys=True)
    ans = q["choices"][q["answer_index"]]
    fields = ("stem", "explanation", "passage")
    if fname.startswith("eng__"):
        lines = q["stem"].split("\n")
        if "並べかえ" in lines[0] and "小文字" not in q["stem"] and any(l.lstrip().startswith(("〔", "[", "(")) for l in lines[1:]):
            lines[0] = lines[0] + NOTE
        if fname == "eng__8.json" and lines[0].startswith("次の 2 文がほぼ同じ意味") and len(lines) >= 3 and not lines[2].startswith("= "):
            lines[2] = "= " + lines[2]
        q["stem"] = "\n".join(lines)
    if fname.startswith("math__"):
        for f in fields:
            q[f] = q.get(f, "").replace("−", "-")
        q["choices"] = [c.replace("−", "-") for c in q["choices"]]
    if fname == "kokugo__33.json":
        for f in fields:
            q[f] = POEM_SP.sub("　", q.get(f, ""))
        q["choices"] = [POEM_SP.sub("　", c) for c in q["choices"]]
    if fname == "shakai__53.json" and any("「てつはう」" in c for c in q["choices"]):
        q["choices"] = [c.replace("「てつはう」", "『てつはう』") for c in q["choices"]]
        for f in fields:
            q[f] = q.get(f, "").replace("「てつはう」", "『てつはう』")
    new_ans = q["choices"][q["answer_index"]]
    # 正解は同じ文字列の置換しか受けていないこと
    canon = lambda t: re.sub(r"\s", "", t).replace("\u2212", "-").replace("\u300e", "\u300c").replace("\u300f", "\u300d")
    assert canon(new_ans) == canon(ans), (fname, ans, new_ans)
    assert len({L.norm_ws(c) for c in q["choices"]}) == 4, (fname, q["choices"])
    return json.dumps(q, ensure_ascii=False, sort_keys=True) != before


changed = 0
seen = {}
for fp in sorted(glob.glob(os.path.join(VD, "*.json"))):
    fname = os.path.basename(fp)
    qs = json.load(open(fp, encoding="utf-8"))
    n = 0
    for q in qs:
        old_stem = q["stem"]
        if fix(q, fname):
            n += 1
            print(f"  {fname}: {old_stem[:40]!r}")
        s = L.sig(q["stem"], q["choices"])
        assert s not in seen, (fname, q["stem"][:40], seen.get(s))
        seen[s] = fname
    changed += n
    if APPLY and n:
        json.dump(qs, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"{'書き戻し' if APPLY else '(表示のみ)'}: {changed} 問")
