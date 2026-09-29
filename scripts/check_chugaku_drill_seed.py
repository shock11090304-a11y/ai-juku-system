#!/usr/bin/env python3
"""🧒 中学ドリルのシード形式ゲート (run_all_gates.py が拾う)。
  - seed-data/chugaku_drill_pool_v1.json  … 中学英語 (subject='chugaku')
  - seed-data/chugaku_math_pool_v1.json   … 中学数学 (subject='chugaku_math')
  - seed-data/chugaku_rika_pool_v1.json   … 中学理科 (subject='chugaku_rika')

固定する不変条件 (壊れると単元ドリルで生徒が誤採点される / 取込で黙って skip される / 範囲外が出る):
  共通: 4 択相異・answer 0〜3・解説に ①〜④ や「選択肢」を書かない・stem 一意・正解位置は単元ごとに 40% 以下・
        unit は scripts/chugaku_dojo/units.json の filter と完全一致 (入試道場の弱点 topic と突き合わせるため)
  英語: 空所 "( )" がちょうど 1 つ・関係代名詞の単元で whose を正解にしない (中学は主格・目的格のみ)・
        whom は誤答にも使わない (中学で一度も出てこない語は見ただけで消せて弁別に寄与しない)
  数学: マイナスは「−」(本文・選択肢に半角 "-" を1つも入れない)・「図のように」等の図を前提にした問題を入れない (画面に図は出せない)・
        高校範囲の語 (sin/cos/tan・判別式・ベクトル・微分積分 など) を入れない
  理科: 半角 "-" を入れない・図/表/グラフを前提にした問題を入れない (本文は1段落・改行なし)・
        高校範囲の語 (物質量・電気陰性度・運動量・比熱・同位体 など) と旧用語 (優性・劣性) を入れない
"""
import collections
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT = json.load(open(os.path.join(REPO, "scripts", "chugaku_dojo", "units.json"), encoding="utf-8"))
UNITS = {s["part"]: [u["filter"] for u in s["units"] if not u.get("reading")] for s in CAT["subjects"]}
POSREF = re.compile(r"[①②③④]|選択肢")
SEEDS = [
    ("chugaku_drill_pool_v1.json", "chugaku", UNITS["eng"], "英語"),
    ("chugaku_math_pool_v1.json", "chugaku_math", UNITS["math"], "数学"),
    ("chugaku_rika_pool_v1.json", "chugaku_rika", UNITS["rika"], "理科"),
]
HS_MATH = re.compile(r"sin|cos|tan|判別式|解と係数|log|数列|ベクトル|微分|積分|余弦定理|正弦定理")
FIGURE = re.compile(r"図のように|下の図|右の図|左の図|次の図")
# 理科: 画面に図・表は出せないので、実験の条件と結果は文章で書く。高校範囲の語と、2021年度の教科書で改められた旧用語も入れない
FIGURE_RIKA = re.compile(r"図のように|下の図|上の図|右の図|左の図|次の図|右図|左図|上図|下図|図[0-9０-９]|表[0-9０-９]|表のように|下の表|右の表|次の表|"
                         r"グラフのように|グラフから|下のグラフ|右のグラフ")
HS_RIKA = re.compile(r"モル|物質量|アボガドロ|電気陰性度|酸化数|電離度|共有結合|イオン結合|金属結合|価電子|イオン化エネルギー|"
                     r"化学平衡|運動方程式|運動量|力積|万有引力|比熱|熱容量|半減期|同位体|フレミング")
OLD_TERM_RIKA = re.compile(r"優性|劣性")


def check_seed(fname, subject, units, kind):
    path = os.path.join(REPO, "seed-data", fname)
    if not os.path.exists(path):
        return [f"{fname}: ファイルが無い"], 0
    qs = json.load(open(path, encoding="utf-8")).get("questions") or []
    bad = []
    seen = {}
    pos = collections.defaultdict(lambda: [0, 0, 0, 0])
    for i, q in enumerate(qs):
        t = f"{fname}#{i}"
        if q.get("subject") != subject:
            bad.append(f"{t}: subject={q.get('subject')!r}")
        if q.get("unit") not in units:
            bad.append(f"{t}: unit={q.get('unit')!r} (カタログに無い)")
        if q.get("level") not in ("basic", "standard", "advanced"):
            bad.append(f"{t}: level={q.get('level')!r}")
        stem = q.get("stem") or ""
        ch = [str(x) for x in (q.get("choices") or [])]
        if len(ch) != 4 or len(set(x.strip() for x in ch)) != 4 or any(not x.strip() for x in ch):
            bad.append(f"{t}: choices={ch}")
        a = q.get("answer")
        if not isinstance(a, int) or not (0 <= a <= 3):
            bad.append(f"{t}: answer={a!r}")
        ex = q.get("explanation") or ""
        if POSREF.search(ex):
            bad.append(f"{t}: 解説に選択肢の位置参照")
        if len(ex) < 40:
            bad.append(f"{t}: 解説が短い ({len(ex)} 字)")
        if kind == "英語":
            if stem.count("( )") != 1:
                bad.append(f"{t}: 空所が {stem.count('( )')} 個")
            if any(re.fullmatch(r"\s*whom\s*", c, re.I) for c in ch) or re.search(r"\bwhom\b", stem, re.I):
                bad.append(f"{t}: whom を使っている")
            if q.get("unit") == "関係代名詞" and isinstance(a, int) and 0 <= a <= 3 and re.fullmatch(r"\s*whose\s*", ch[a], re.I):
                bad.append(f"{t}: 関係代名詞 whose を正解にしている (中学範囲外)")
        elif kind == "理科":
            for part in [stem] + ch:
                if "-" in part:
                    bad.append(f"{t}: 半角の - がある (マイナスは「−」): {part[:30]}")
                if HS_RIKA.search(part):
                    bad.append(f"{t}: 高校範囲の語: {part[:30]}")
                if OLD_TERM_RIKA.search(part):
                    bad.append(f"{t}: 旧用語 (優性・劣性ではなく顕性・潜性): {part[:30]}")
            if FIGURE_RIKA.search(stem) or "\n" in stem:
                bad.append(f"{t}: 図・表を前提にしている / 本文に改行")
        else:
            for part in [stem] + ch:
                if "-" in part:   # 文字に隣接した 3x-2 も拾うため、正規表現でなく「半角 - が1つも無い」で見る
                    bad.append(f"{t}: 半角の - がある (マイナスは「−」): {part[:30]}")
                if HS_MATH.search(part):
                    bad.append(f"{t}: 高校範囲の語: {part[:30]}")
            if FIGURE.search(stem):
                bad.append(f"{t}: 図を前提にしている")
        k = stem.strip()
        if k in seen:
            bad.append(f"{t}: stem が #{seen[k]} と重複")
        seen[k] = i
        if isinstance(a, int) and 0 <= a <= 3:
            pos[q.get("unit")][a] += 1
    for u in units:
        v = pos.get(u, [0, 0, 0, 0])
        if sum(v) == 0:
            bad.append(f"{fname}: 単元 {u} が 0 問")
        elif max(v) / sum(v) > 0.40:
            bad.append(f"{fname}: 単元 {u} の正解位置が偏っている {v}")
    print(f"{fname}: {len(qs)} 問 / {len([u for u in units if sum(pos.get(u, [0]*4))])} 単元")
    return bad, len(qs)


def main():
    allbad = []
    for fname, subject, units, kind in SEEDS:
        bad, _n = check_seed(fname, subject, units, kind)
        allbad += bad
    if allbad:
        print(f"❌ VIOLATION {len(allbad)} 件")
        for b in allbad[:60]:
            print("  -", b)
        sys.exit(1)
    print("✅ ALL PASS (中学ドリルのシード形式)")


if __name__ == "__main__":
    main()
