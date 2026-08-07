#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""content_ia_jaku から診断マップ `diagnosis_ia_jaku.py` を生成する。

  python3 gen_diagnosis_ia_jaku.py

スキルの割り当て(skill/sub)は問題データ側に書いてあるので、ここは
「印刷版と同じ採番」に並べ替えて書き出すだけ。★問題を増減・並替・改稿したら必ず回す
(analyze_ia_jaku.py が本文先頭40字を照合してドリフトを検知し、ズレていたら止まる)。
"""
import os, pprint
import _ia_jaku_lib as L
import content_ia_jaku as C
import build_kiso as K

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "diagnosis_ia_jaku.py")
HEAD_LEN = 40


def main():
    for p in C.PARTS:
        K.reorder(p["units"])          # build と同じ規則で採番
    units_info, mp = [], {}
    for code, u in zip(C.CODES, C.UNITS):
        units_info.append({"code": code, "name": u["name"], "count": len(u["problems"])})
        for j, q in enumerate(u["problems"], 1):
            mp[f"{code}-{j}"] = {
                "skill": q["skill"],
                "sub": list(q["sub"]),
                "level": q["level"],
                "group": q.get("group", ""),
                "head": q["stem"][:HEAD_LEN],
            }
    body = f'''# -*- coding: utf-8 -*-
"""数学I·A 弱点発見トレーニング の【塾長用】弱点診断マップ。
★生徒には見せない(どの問題が何を測るかを知られると診断精度が落ちる)。
MAP のキーは「単元コード-問題番号」(印刷版の番号と同一・接頭辞 A 必須)。
head は content_ia_jaku とのドリフト検知用(先頭{HEAD_LEN}字)。

★このファイルは自動生成。手で編集しない → `python3 gen_diagnosis_ia_jaku.py`
"""
from _ia_jaku_lib import SKILLS, PREREQ   # noqa: F401  (analyze 側が参照する)

LEVEL_W = {{'basic': 1.5, 'standard': 1.0, 'advanced': 0.6}}   # 基礎ミスほど重い
ROLE_W = {{'primary': 1.0, 'sub': 0.4}}

UNITS_INFO = {pprint.pformat(units_info, width=100, sort_dicts=False)}

MAP = {pprint.pformat(mp, width=100, sort_dicts=False)}
'''
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(body)
    used = {m["skill"] for m in mp.values()} | {c for m in mp.values() for c in m["sub"]}
    unused = [c for c in L.SKILLS if c not in used]
    print(f"WROTE {OUT} | units: {len(units_info)} | problems: {len(mp)} | skills used: {len(used)}/{len(L.SKILLS)}")
    if unused:
        # ★「弱点特化で分野を絞ると、その分野外のスキルが丸ごと落ちる」のを機械で見る。
        print(f"  ! 1問も担当が無いスキル({len(unused)}): "
              + "、".join(f"{c}({L.SKILLS[c]})" for c in unused))


if __name__ == "__main__":
    main()
