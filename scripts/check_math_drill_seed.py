#!/usr/bin/env python3
"""📐 seed-data/math_drill_*.json (高校数学ドリル・科目 math) の形式ゲート (run_all_gates.py が拾う)。

固定する不変条件 (壊れると単元ドリルで生徒が誤採点される / 数式が生の文字で出る / 取込で黙って skip される):
  - subject は 'math'、level は basic / standard / advanced、unit は入試道場の単元タイル (dojo-drill.html の topic) と同じ文字列
    (道場にタイルが無い単元は EXTRA_UNITS に明記したものだけ)
    (math は server 側に単元の許可リストが無いので、綴り違いはここで止める。弱点が道場とドリルで別の行になるのを防ぐ)
  - choices は 4 つ相異・空でない、answer は 0〜3
  - 解説は 20 字以上で、選択肢の番号・記号 (⓪①…・選択肢2・アの解答群) を書かない (値で書く)
  - 前後の問を指さない (「上の確率変数」「次の問」…)・問題文で定義していない (ア)〜(エ) を解説で使わない
  - stem に図への言及が無い (画面に図は出せない)
  - 数式の区切り \\( \\) の数が合う・生成元の独自記法 ([[f|..]] <sub> <super>) が残っていない
  - stem は全シードを通して一意 (取込の dedup は stem+unit+subject)
  - 正解位置は単元ごとに散らす (10 問以上の単元で、どの位置も 40% 以下)
  - 選択肢がすべて数値の問題では、正解の値の順位 (小さい方から何番目か) も散らす (10 問以上で、どの順位も 40% 以下)。
    表示の位置を散らしても「2 番目に大きい値を選ぶ」で当たるのを防ぐ (2026-10-06 共通テスト型で 45% だった)
  - $ を使わない (mypage・class.html では $ も数式の区切り。CEO のプレビューは \( \) だけを描く)
  - 単元名の照合先 dojo-drill.html が無ければ落とす (黙って照合を飛ばさない)。5 問未満の単元は表示だけ (単元配信は 5 問から)
"""
import collections
import fractions
import glob
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEEDS = sorted(glob.glob(os.path.join(REPO, "seed-data", "math_drill_*.json")))
UNITS = {
    "基礎数学 二次関数", "基礎数学 データ", "基礎数学 図形と計量", "数学I 数と式", "数学I 集合と命題",
    "基礎数学 確率", "基礎数学 整数", "数学A 図形の性質",
    "基礎数学 微積", "基礎数学 三角関数", "基礎数学 指数対数", "数学II 式と証明", "数学II 図形と方程式",
    "基礎数学 数列", "数学B 統計的な推測",
    "数学III 極限", "数学III 微分法", "数学III 積分法",
    "基礎数学 ベクトル", "数学C 複素数平面", "数学C 平面上の曲線",
}
# 入試道場にタイルが無い単元 (問題集にはあるので足す)。道場の topic とは照合しない
EXTRA_UNITS = {"数学II 複素数と方程式"}
LEVELS = {"basic", "standard", "advanced"}
NUMREF = re.compile(r"[⓪①②③④]|選択肢\s*[0-9０-９]|[アイウエ](?:の解答群|が正解)")
FIGURE = re.compile(r"図(?:のように|は|に示|の(?:よう|ような|中|三角形|点))|下の図|右の図|左の図")
LEFTOVER = re.compile(r"\[\[|<sub>|<super>|</?b>|\x00")
# 1 問ずつ出るので、前後の問を指す言い回しは使えない (2026-10-06 「上の確率変数 X」で分布が無い問題が盲検 3 名に見つかった)
XREF = re.compile(r"前の問|前問|次の問|下の問|上の問|上の確率変数")
# 選択肢に記号は付かないので、問題文で定義していない (ア)〜(エ) を解説で使わない (問題集の記号つき選択肢の名残)
LABEL = re.compile(r"[(（]([アイウエ])[)）]")


def numeric_value(c):
    """選択肢が 1 つの数 (整数・小数・\\frac{整数}{整数}・単位つき) なら値を返す。それ以外は None。"""
    t = re.sub(r"(個|円|分|人| ?m)$", "", str(c).strip()).strip()
    m = re.fullmatch(r"(-?)\\\(\\frac\{(\d+)\}\{(\d+)\}\\\)", t)
    if m:
        return (-1 if m.group(1) else 1) * fractions.Fraction(int(m.group(2)), int(m.group(3)))
    if re.fullmatch(r"-?\d+(?:\.\d+)?", t):
        return fractions.Fraction(t)
    return None


def main():
    if not SEEDS:
        print("❌ seed-data/math_drill_*.json が 1 本も無い")
        sys.exit(1)
    dojo = os.path.join(REPO, "dojo-drill.html")
    if not os.path.exists(dojo):
        print("❌ dojo-drill.html が無いので単元名を入試道場の topic と照合できない")
        sys.exit(1)
    topics = set(re.findall(r"topic:\s*'([^']+)'", open(dojo, encoding="utf-8").read()))
    missing = sorted(u for u in UNITS if u not in topics)
    if not topics or missing:
        print(f"❌ ゲートの単元表が入試道場の topic に無い: {missing or '(topic を 1 つも読めない)'}")
        sys.exit(1)
    bad = []
    seen = {}
    total = 0
    for seed in SEEDS:
        name = os.path.basename(seed)
        d = json.load(open(seed, encoding="utf-8"))
        qs = d.get("questions") or []
        pos = collections.defaultdict(lambda: [0, 0, 0, 0])
        ranks = [0, 0, 0, 0]
        per_unit = collections.Counter()
        for q in qs:
            per_unit[q.get("unit")] += 1
            total += 1
            src = f"{name}:{q.get('source', '?')}"
            if q.get("subject") != "math":
                bad.append(f"{src}: subject={q.get('subject')!r}")
            if q.get("unit") not in UNITS and q.get("unit") not in EXTRA_UNITS:
                bad.append(f"{src}: unit={q.get('unit')!r} (入試道場の topic と違う)")
            if q.get("level") not in LEVELS:
                bad.append(f"{src}: level={q.get('level')!r}")
            stem = q.get("stem") or ""
            ch = q.get("choices") or []
            a = q.get("answer")
            ex = q.get("explanation") or ""
            if not stem.strip():
                bad.append(f"{src}: stem が空")
            if len(ch) != 4 or not all(isinstance(c, str) and c.strip() for c in ch) or len({c.strip() for c in ch}) != 4:
                bad.append(f"{src}: choices={ch}")
            if not isinstance(a, int) or not (0 <= a <= 3):
                bad.append(f"{src}: answer={a!r}")
            elif q.get("unit") in UNITS or q.get("unit") in EXTRA_UNITS:
                pos[q["unit"]][a] += 1
            if len(ex) < 20:
                bad.append(f"{src}: 解説が短い ({len(ex)} 字)")
            if NUMREF.search(ex + stem):
                bad.append(f"{src}: 選択肢の番号・記号の参照: {NUMREF.search(ex + stem).group(0)}")
            if XREF.search(stem + ex):
                bad.append(f"{src}: 前後の問を指す言い回し: {XREF.search(stem + ex).group(0)}")
            stem_labels = set(LABEL.findall(stem))
            if any(l not in stem_labels for l in LABEL.findall(ex)):
                bad.append(f"{src}: 解説が問題文に無い記号 ({''.join(sorted(set(LABEL.findall(ex)) - stem_labels))}) を指す")
            if FIGURE.search(stem):
                bad.append(f"{src}: stem に図への言及: {FIGURE.search(stem).group(0)}")
            for part, t in [("stem", stem), ("explanation", ex)] + [(f"choice{i}", c) for i, c in enumerate(ch) if isinstance(c, str)]:
                if t.count("\\(") != t.count("\\)"):
                    bad.append(f"{src}: {part} の \\( \\) の数が合わない")
                if LEFTOVER.search(t):
                    bad.append(f"{src}: {part} に生成元の記法が残る: {LEFTOVER.search(t).group(0)}")
                if "$" in t:
                    bad.append(f"{src}: {part} に $ (mypage・class.html では数式の区切りになる。\\( \\) で書く)")
            vals = [numeric_value(c) for c in ch] if len(ch) == 4 else []
            if vals and all(v is not None for v in vals) and len(set(vals)) == 4 and isinstance(a, int) and 0 <= a <= 3:
                ranks[sorted(vals).index(vals[a])] += 1
            k = stem.strip()
            if k in seen:
                bad.append(f"{src}: stem が {seen[k]} と重複")
            seen[k] = src
        for u, v in pos.items():
            if sum(v) >= 10 and max(v) / sum(v) > 0.40:
                bad.append(f"{name}: 単元 {u} の正解位置が偏っている {v}")
        if sum(ranks) >= 10 and max(ranks) / sum(ranks) > 0.40:
            bad.append(f"{name}: 数値の選択肢で正解の順位 (小さい方から 0〜3) が偏っている {ranks}")
        small = sorted(u for u, n in per_unit.items() if n < 5)
        print(f"{name}: {len(qs)} 問 / 単元 {len(pos)} / 数値の選択肢の正解順位 {ranks}"
              + (f" / 5 問未満の単元 (単元配信は不可・科目まるごとでは出る): {small}" if small else ""))
    if bad:
        print(f"❌ VIOLATION {len(bad)} 件")
        for b in bad[:80]:
            print("  -", b)
        sys.exit(1)
    print(f"✅ ALL PASS (高校数学ドリル シードの形式・{total} 問)")


if __name__ == "__main__":
    main()
