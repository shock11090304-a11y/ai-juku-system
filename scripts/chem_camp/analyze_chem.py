#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""化学［理論］総復習トレーニングの自己採点結果を診断する（塾長用）。

  python3 analyze_chem.py --name "生徒名" --save --hint "C09-4 C13-5" C05-3 C11-4 C15-2

  位置引数 … ×だった問題番号(C05-3 の形。C は省略可・"5-3" でもよい)
  --hint   … △(解説や公式を見てから正解した)の番号。重み0.5の誤答として集計する
  --save   … レポートを 弱点分析_化学_<名前>_<日付>.txt に保存する

出力は塾長用。スキル名は生徒に言わず、「まず C13-3 をもう一度」と番号だけ伝える。
"""
import os, sys, re, argparse, datetime, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import diagnosis_chem as D                                   # noqa: E402

LEVEL_JA = {"basic": "基礎", "standard": "標準", "advanced": "発展"}


def norm(pid):
    """'c05-3' / 'C5-3' → 'C05-3'。★C は必須。

    C を省略可にすると "18-3" が化学 C18-3 として黙って通る。この生徒は同時期に
    数学「第2集」(単元13〜27)も解いていて、そちらのシートは C 無しの "18-3" 形式。
    数学の番号を貼り間違えても検出されず、別の問題を弱点と誤診断してしまう。
    """
    m = re.fullmatch(r"[Cc]0*(\d{1,2})[-‐−]0*(\d)", pid.strip())
    if not m:
        return None
    return f"C{int(m.group(1)):02d}-{int(m.group(2))}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("wrong", nargs="*", help="×だった番号")
    ap.add_argument("--hint", default="", help="△だった番号(スペース区切り)")
    ap.add_argument("--name", default="")
    ap.add_argument("--save", action="store_true")
    a = ap.parse_args()

    idx = D.index()
    wrong, hint, bad = [], [], []
    for s in a.wrong:
        p = norm(s)
        (wrong if p in idx else bad).append(p or s)
    for s in a.hint.split():
        p = norm(s)
        (hint if p in idx else bad).append(p or s)
    if bad:
        sys.exit(f"存在しない問題番号: {bad}\n"
                 "  化学は C05-3 のように C を付けてください(C01-1〜C18-6)。\n"
                 "  C の無い 05-3 形式は数学の第2集(単元13〜27)です。そちらは\n"
                 "  scripts/math_workbook/analyze_kiso.py で診断してください。")

    # 重み: × = 1.0, △ = 0.5
    w = collections.defaultdict(float)
    for p in wrong:
        w[p] = 1.0
    for p in hint:
        w[p] = max(w[p], 0.5)

    total = len(idx)
    miss = len(wrong) + 0.5 * len(hint)
    L = []
    L.append("=" * 62)
    L.append(f"◆ 弱点分析レポート【塾長用・生徒非公開】  {datetime.date.today()}")
    L.append(f"  生徒: {a.name or '(未指定)'}   教材: 化学［理論］総復習トレーニング")
    L.append(f"  誤答 {len(wrong)}問 / 出題 {total}問 (正答率 {100*(1-miss/total):.0f}%)"
             f"   △{len(hint)}問(解説を見て正解=自力ではない・重み0.5で誤答に算入)")
    L.append("=" * 62)

    # ---- 単元別
    L.append("\n【1】単元別の成績")
    by_unit = collections.defaultdict(list)
    for pid, q in idx.items():
        by_unit[q["unit"]].append(pid)
    cur_area = None
    for uno in sorted(by_unit):
        pids = by_unit[uno]
        info = idx[pids[0]]
        if info["area"] != cur_area:
            cur_area = info["area"]
            L.append(f"  《{cur_area}》")
        ng = [p for p in pids if p in wrong]
        hn = [p for p in pids if p in hint]
        score = sum(w[p] for p in pids)
        mark = "★" if score >= len(pids) * 0.5 else ("・" if score else "  ")
        tail = f"   [{' '.join(x.split('-')[1] for x in ng)}]" if ng else ""
        tail += f"   △[{' '.join(x.split('-')[1] for x in hn)}]" if hn else ""
        nm = info['unit_name'].split('【')[0]
        # 全角は2桁ぶんの幅を取るので、単純な :<28 では列が揃わない
        pad = " " * max(0, 34 - sum(2 if ord(c) > 0x2000 else 1 for c in nm))
        L.append(f"  {mark} C{uno:02d} {nm}{pad}誤答 {len(ng)}/{len(pids)}{tail}")

    # ---- スキル別
    L.append("\n【2】弱点スキル(裏タグ集計・生徒には見せない)")
    sk_all, sk_bad = collections.defaultdict(list), collections.defaultdict(list)
    for pid, q in idx.items():
        sk_all[q["skill"]].append(pid)
        if w[pid]:
            sk_bad[q["skill"]].append(pid)
    ranked = sorted(sk_bad.items(),
                    key=lambda kv: -sum(w[p] for p in kv[1]) / len(sk_all[kv[0]]))
    for sk, pids in ranked:
        rate = sum(w[p] for p in pids) / len(sk_all[sk])
        tag = "[弱点]" if rate >= 0.6 else "[要注意]"
        L.append(f"  {tag} {sk} ({rate*100:.0f}%)  誤答: {' '.join(sorted(pids))}")
    if not ranked:
        L.append("  (誤答なし)")

    # ---- 根っこ
    # 「根っこ」= 落ちているスキルのうち、他の落ちているスキルの土台になっているもの。
    # 土台が無事なのに単発で落ちているものは根っこではない(そこだけ解き直せばよい)ので分けて出す。
    L.append("\n【3】つまずきの根っこ(推定)")
    weak = {sk for sk, pids in sk_bad.items()
            if sum(w[p] for p in pids) / len(sk_all[sk]) >= 0.5}
    roots = {x for s in weak for x in D.PREREQ.get(s, []) if x in weak}
    downstream = {s for s in weak if set(D.PREREQ.get(s, [])) & weak}
    isolated = sorted(weak - roots - downstream)
    for r in sorted(roots):
        kids = sorted(s for s in weak if r in D.PREREQ.get(s, []))
        L.append(f"  ● {r} が根っこ  → ここが崩れているので {' / '.join(kids)} も直らない")
    if not roots:
        L.append("  (連鎖している弱点は無い。下の単発の穴を個別に埋めればよい)")
    if isolated:
        L.append("  ○ 単発の穴(土台は無事・そこだけ解き直せばよい): " + " / ".join(isolated))

    # ---- 処方
    L.append("\n【4】復習の処方(この順で)")
    n = 1
    for r in sorted(roots):
        same = sorted(sk_all[r])
        L.append(f"  {n}. 「{r}」を土台からやり直す: "
                 + " ".join(p + ("×" if p in wrong else ("△" if p in hint else "")) for p in same))
        n += 1
    for sk in isolated:
        same = sorted(sk_all[sk])
        L.append(f"  {n}. 「{sk}」を解き直す: "
                 + " ".join(p + ("×" if p in wrong else ("△" if p in hint else "")) for p in same))
        n += 1
    if wrong or hint:
        L.append(f"  {n}. 最後に誤答全問を解き直し: {' '.join(sorted(set(wrong) | set(hint)))}")
        L.append("     (日をあけて2回目。2回連続○になったら卒業)")

    # ---- 声かけ
    L.append("\n【5】生徒への声かけ例(スキル名は口にしない)")
    for r in (sorted(roots) + isolated)[:3]:
        ex = [p for p in sorted(sk_all[r]) if w[p]][:2]
        if ex:
            L.append(f"  ・「まず {' と '.join(ex)} をもう一回だけやってみようか」(狙い: {r})")

    L.append("\n" + "-" * 62)
    L.append("注: このレポート・診断キー・analyze_chem.py は生徒に渡さない。")
    out = "\n".join(L)
    print(out)
    if a.save:
        f = os.path.join(HERE, f"弱点分析_化学_{a.name or 'noname'}_{datetime.date.today():%Y%m%d}.txt")
        open(f, "w", encoding="utf-8").write(out + "\n")
        print(f"\nSAVED {f}")


if __name__ == "__main__":
    main()
