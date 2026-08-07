#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数学I·A 弱点発見トレーニング の【塾長用】弱点分析CLI。

生徒の×だった問題番号(印刷版の「A01-3」形式)を入れると、
どのスキルが弱いか・つまずきの根っこはどこか・何を復習させるかを出力する。
★出力レポートと diagnosis_ia_jaku.py は生徒に見せない。

使い方:
  python3 analyze_ia_jaku.py A06-3 A07-1 A07-5
  python3 analyze_ia_jaku.py --name 生徒名 --save A03-2 A09-4
  python3 analyze_ia_jaku.py --hint "A11-2 A11-6" A12-1   # △(公式を見て正解)も渡す
  python3 analyze_ia_jaku.py --skip A18 A09-4             # 単元A18まるごと未実施
  python3 analyze_ia_jaku.py --skip "A18-7 A18-8" A09-4   # 問題単位の未実施(引用符必須)

★番号の接頭辞 A は必須。付けないとエラーにする —— 「13-4」を黙って受け付けると、
  同時期に解いている第2集(単元13〜27)や化学(C01〜C18)の番号を貼り間違えても検出できない。
"""
import sys, os, re, datetime, unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import diagnosis_ia_jaku as D

WEAK_TH, WATCH_TH = 0.5, 0.25
UP_TH = 0.6                 # 「標準以上だけ」のスコアがこれ以上なら弱点(基礎重み 1.5 の副作用への保険)
MIN_WEAK_WRONG = 2          # 弱点断定には誤答2問以上の証拠を要求(1問なら「要再測」)
HINT_W = 0.5                # △(公式を見て解けた)は「半分できていない」として数える
LEVEL_JA = {"basic": "基礎", "standard": "標準", "advanced": "発展"}
LEVEL_ORD = {"basic": 0, "standard": 1, "advanced": 2}
BOOK = "数学I·A 弱点発見トレーニング"

Z2H = str.maketrans("０１２３４５６７８９ＡａA－ー−‐―〜、，", "0123456789AAA------,,")

UNIT_ORDER = [u["code"] for u in D.UNITS_INFO]
UNIT_NAME = {u["code"]: u["name"] for u in D.UNITS_INFO}
UNIT_SIZE = {u["code"]: u["count"] for u in D.UNITS_INFO}
# 編(area) は _ia_jaku_lib.PLAN が持つ
from _ia_jaku_lib import PLAN                      # noqa: E402
AREA_OF = {c: a for c, _n, _cnt, a in PLAN}
AREAS = []
for _c in UNIT_ORDER:
    if AREA_OF[_c] not in AREAS:
        AREAS.append(AREA_OF[_c])


def parse_refs(tokens, expand_units=False):
    """'A07-3' 'a7-3' 'Ａ０７−３' 'A,B' 混在を 'A07-3' 形式の list へ。
    expand_units=True なら 'A18' だけの指定を単元A18の全問に展開(--skip用)。"""
    refs = []
    for tk in tokens:
        for piece in tk.translate(Z2H).replace(",", " ").split():
            p = piece.upper()
            m = re.fullmatch(r"A(\d{1,2})-(\d{1,2})", p)
            if m:
                code = f"A{int(m.group(1)):02d}"
                if code not in UNIT_SIZE:
                    raise ValueError(f"単元 {code} は存在しません({UNIT_ORDER[0]}〜{UNIT_ORDER[-1]})")
                refs.append(f"{code}-{int(m.group(2))}")
                continue
            m = re.fullmatch(r"A(\d{1,2})", p)
            if m and expand_units:
                code = f"A{int(m.group(1)):02d}"
                if code not in UNIT_SIZE:
                    raise ValueError(f"単元 {code} は存在しません({UNIT_ORDER[0]}〜{UNIT_ORDER[-1]})")
                refs.extend(f"{code}-{j}" for j in range(1, UNIT_SIZE[code] + 1))
                continue
            if re.fullmatch(r"\d{1,2}(-\d{1,2})?", p):
                raise ValueError(
                    f"「{piece}」に接頭辞 A がありません。この教材の番号は A07-3 の形です"
                    "（数字だけだと第2集や化学の番号と区別できず、誤診断になります）")
            hint = "。単元まるごとは --skip A18 のように単元コードだけでも指定できます" if not expand_units else ""
            raise ValueError(f"番号の形式が不正です: 「{piece}」(例: A07-3){hint}")
    return refs


def validate_against_content():
    """content と診断マップのドリフト検知。印刷版とデータ版のズレを許さない。"""
    import content_ia_jaku as C
    import build_kiso as K
    for p in C.PARTS:
        K.reorder(p["units"])
    problems = {f"{code}-{j}": q
                for code, u in zip(C.CODES, C.UNITS)
                for j, q in enumerate(u["problems"], 1)}
    if set(problems) != set(D.MAP):
        miss = sorted(set(problems) ^ set(D.MAP))[:6]
        sys.exit(f"★診断マップと問題集がズレています(問題の増減: {miss})。"
                 "python3 gen_diagnosis_ia_jaku.py を回してください。")
    for key, q in problems.items():
        m = D.MAP[key]
        # ★skill/sub も照合する。ここを見ないと、parts のスキルタグを直して
        #   gen_diagnosis を回し忘れたとき、ゲート緑のまま古いタグで診断が出る。
        #   head(先頭40字)は A05-1/A05-2 のように衝突する組があり、単独では指紋にならない。
        if (q["stem"][:len(m["head"])] != m["head"] or q.get("level", "") != m["level"]
                or q.get("group", "") != m["group"] or q.get("skill") != m["skill"]
                or list(q.get("sub", [])) != list(m["sub"])):
            sys.exit(f"★診断マップと問題集がズレています({key} の 本文/レベル/group/skill/sub のいずれかが不一致)。"
                     "python3 gen_diagnosis_ia_jaku.py を回してください。")


def skill_probs_all():
    """スキル → 担当する全問題ref(primary+sub、skip除外なし)。処方リスト用。"""
    out = {s: [] for s in D.SKILLS}
    for key, m in D.MAP.items():
        out[m["skill"]].append(key)
        for c in m["sub"]:
            out[c].append(key)
    return out


def skill_stats(wrong, skip, hint=frozenset()):
    """スキルごとに (誤答重み, 全体重み, 誤答ref) を集計。skipは分子分母とも除外。
    あわせて「標準以上だけ」のスコア(up_score)も出す(classify の2つ目の入口)。"""
    stats = {s: {"m": 0.0, "t": 0.0, "um": 0.0, "ut": 0.0, "un": 0,
                 "wrong": [], "hint": [], "pev": 0}
             for s in D.SKILLS}
    for key, m in D.MAP.items():
        if key in skip:
            continue
        lw = D.LEVEL_W.get(m["level"], 1.0)
        upper = m["level"] != "basic"
        for role, code in [("primary", m["skill"])] + [("sub", c) for c in m["sub"]]:
            w = D.ROLE_W[role] * lw
            st = stats[code]
            st["t"] += w
            if upper:
                st["ut"] += w
                st["un"] += 1
            if key in wrong:
                st["m"] += w
                if upper:
                    st["um"] += w
                st["wrong"].append(key)
                if role == "primary":
                    st["pev"] += 1
            elif key in hint:
                st["m"] += w * HINT_W
                if upper:
                    st["um"] += w * HINT_W
                st["hint"].append(key)
                if role == "primary":
                    st["pev"] += 1
    for st in stats.values():
        st["score"] = st["m"] / st["t"] if st["t"] > 0 else 0.0
        st["up_score"] = st["um"] / st["ut"] if st["ut"] > 0 else 0.0
    return stats


def classify(stats):
    """弱点(証拠2問以上) / 要注意(1問のみの高スコア含む) に分類。

    ★2つ目の入口 UP_TH がある理由: LEVEL_W は基礎を 1.5 で最も重くしているので、
      「基礎は取れるが標準以上は全滅」の生徒はスコアが 0.5 に届かない
      (実測で SK4=32% / SK1=34% / QF1=45% など13スキルが素通りした)。
      この層こそ本教材の主対象なので、**標準以上だけのスコア**でも判定する。
    """
    weak, watch = {}, {}
    for s, st in stats.items():
        if not st["wrong"] and not st["hint"]:
            continue
        ev = len(st["wrong"]) + len(st["hint"])
        # ★up 経路は (a) そのスキルを**主スキル**とする問題で落としている
        #   (b) 標準以上の担当が2問以上ある —— の両方を要求する。
        #   (a) が無いと「自分の問題は全問正解なのに副担当の誤答だけで弱点」が出る(実測6件)。
        #   (b) が無いと --skip で標準以上が1問しか残らないとき up=1.0 に跳ねる。
        # ★「主スキルとしての誤答が1問もない」スキルは、どちらの経路でも弱点にしない。
        #   副スキル重み 0.4 でも副担当が多いスキルは score が 0.5 を超える。実測で
        #   DA3(69%)/TR3(67%)/CP2(62%)/CP4(56%)/TR4(52%)/IN5(50%) の6件が、
        #   主担当を全問正解していても「根っこ」と断定され処方の先頭に来ていた。
        if st["pev"] < 1:
            if st["score"] >= WATCH_TH:
                watch[s] = (st["score"], "主スキルの誤答なし・副担当のみ")
            continue
        up = st["up_score"] if st["un"] >= 2 else 0.0
        hit = st["score"] >= WEAK_TH or up >= UP_TH
        if ev >= MIN_WEAK_WRONG and hit:
            # ★以前は score<WATCH_TH のとき up を捨てていたため、up で弱点にしたスキルを
            #   up を無視して最下位に並べ、根っこにも処方にも上がらなかった。素直に大きい方を採る。
            weak[s] = max(st["score"], up)
        elif hit:
            # ★ここも max を採る。score だけ入れると、up で拾ったスキルが 11% などと
            #   過小表示され、watch を score 順に並べる処方・根っこ候補で下位に沈む。
            watch[s] = (max(st["score"], up),
                        "誤答1問のみ・要再測" if ev < MIN_WEAK_WRONG else "証拠不足")
        elif st["score"] >= WATCH_TH:
            watch[s] = (st["score"], "")
    return weak, watch


def find_roots(weak, watch=None):
    """弱いスキルのうち、前提スキルがどれも崩れていないもの=根っこ。

    ★前提スキルの探索を weak だけに限ると、前提が [要注意] 止まりのときに
      連鎖が切れて**子スキルが根っこに昇格する**(平方完成を8問落としている生徒に
      「根っこは最大最小」と報告し、処方にも平方完成が一度も出なかった)。
      要注意も「崩れている候補」として辿る。
    """
    shaky = set(weak) | set(watch or {})
    return [s for s in weak if not any(p in shaky for p in D.PREREQ.get(s, []))]


def upstream_watch(weak, watch):
    """weak の前提のうち、watch 止まりのもの(=根っこの可能性が高いが証拠が足りない)。"""
    out = {}
    for s in weak:
        for p in D.PREREQ.get(s, []):
            if p in watch and p not in weak:
                out.setdefault(p, []).append(s)
    return out


def downstream(root, weak):
    """root を前提に持つ(推移的)弱スキル=連鎖して崩れている先。"""
    out, frontier = set(), {root}
    while frontier:
        nxt = set()
        for s in weak:
            if s in out or s in frontier:
                continue
            if any(p in frontier or p in out for p in D.PREREQ.get(s, [])):
                nxt.add(s)
        out |= nxt
        frontier = nxt
    return sorted(out, key=lambda s: -weak[s])


def area_concentration(wrong):
    """編単位の「広く浅い崩れ」検出。誤答の2/3以上が同一編・4問以上・2単元以上に分散
    → 単元を絞らず編まるごと再点検を勧める。"""
    notes = []
    for area in AREAS:
        codes = {c for c in UNIT_ORDER if AREA_OF[c] == area}
        aw = [r for r in wrong if r.split("-")[0] in codes]
        aunits = {r.split("-")[0] for r in aw}
        if len(aw) >= 4 and len(aw) * 3 >= len(wrong) * 2 and len(aunits) >= 2:
            notes.append(f"  ● {area}全体に誤答が分散({len(aw)}問・{len(aunits)}単元) "
                         f"→ 単元を絞らずこの編を頭から基礎再点検")
    return notes


def pad_ja(s, width):
    w = sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in s)
    return s + " " * max(0, width - w)


def ref_sort(r):
    c, j = r.split("-")
    return (UNIT_ORDER.index(c), int(j))


def build_report(name, wrong, skip, stats, hint=frozenset()):
    all_probs = skill_probs_all()
    total = len(D.MAP) - len(skip)
    lines = []
    add = lines.append
    today = datetime.date.today().strftime("%Y-%m-%d")
    add("=" * 66)
    add(f"◆ 弱点分析レポート【塾長用・生徒非公開】  {today}")
    add(f"  生徒: {name or '(無記名)'}   教材: {BOOK}")
    jiriki = total - len(wrong) - len(hint)
    add(f"  誤答 {len(wrong)}問 / 出題 {total}問 "
        f"(正答率 {round(100 * (total - len(wrong)) / total)}%"
        + (f" ・自力正解だけなら {round(100 * jiriki / total)}%" if hint else "") + ")"
        + (f"   △{len(hint)}問(公式を見て正解=自力ではない・重み{HINT_W}で誤答に算入)" if hint else "")
        + (f"   未実施 {len(skip)}問は除外" if skip else ""))
    add("=" * 66)

    # ① 単元別
    add("\n【1】単元別の成績")
    cur_area = None
    for code in UNIT_ORDER:
        if AREA_OF[code] != cur_area:
            cur_area = AREA_OF[code]
            add(f"  《{cur_area}》")
        refs = sorted([r for r in wrong if r.startswith(code + "-")], key=ref_sort)
        hrefs = sorted([r for r in hint if r.startswith(code + "-")], key=ref_sort)
        cnt = UNIT_SIZE[code] - sum(1 for r in skip if r.startswith(code + "-"))
        if cnt == 0:
            add(f"      {code} {pad_ja(UNIT_NAME[code], 30)}(未実施)")
            continue
        load = len(refs) + HINT_W * len(hrefs)
        mark = "★" if load / cnt >= 0.4 else (" " if not refs and not hrefs else "・")
        add(f"    {mark} {code} {pad_ja(UNIT_NAME[code], 30)}誤答 {len(refs)}/{cnt}"
            + (f"（△{len(hrefs)}）" if hrefs else "")
            + (f"   [{' '.join(refs)}]" if refs else "")
            + (f"  △[{' '.join(hrefs)}]" if hrefs else ""))

    # ② スキル判定
    weak, watch = classify(stats)
    add("\n【2】弱点スキル(裏タグ集計・生徒には見せない)")
    if not wrong and not hint:
        add("  全問正解です。この教材の範囲に弱点はありません。")
    elif not wrong:
        add("  ×はありませんが、△(公式を見て解けた)が残っています。自力で解けるまで詰めましょう。")
    elif not weak and not watch:
        add("  弱点と言えるスキルはありません。誤答は単発ミスの範囲です。")
    for s in sorted(weak, key=lambda x: -weak[x]):
        st = stats[s]
        chain = [p for p in D.PREREQ.get(s, []) if p in weak]
        tag = f" ← 根っこは「{'・'.join(D.SKILLS[p] for p in chain)}」の連鎖" if chain else ""
        hs = f"  △: {' '.join(sorted(st['hint'], key=ref_sort))}" if st["hint"] else ""
        ws = f"  誤答: {' '.join(sorted(st['wrong'], key=ref_sort))}" if st["wrong"] else ""
        up = (f"  [標準以上 {round(st['up_score'] * 100)}%]"
              if st["up_score"] >= UP_TH and st["pev"] >= 1 and st["un"] >= 2 else "")
        add(f"  [弱点] {D.SKILLS[s]} ({s})  {round(st['score'] * 100)}%{up}{ws}{hs}{tag}")
    for s in sorted(watch, key=lambda x: -watch[x][0]):
        st = stats[s]
        score, note = watch[s]
        tag = f" ({note})" if note else ""
        hs = f"  △: {' '.join(sorted(st['hint'], key=ref_sort))}" if st["hint"] else ""
        ws = f"  誤答: {' '.join(sorted(st['wrong'], key=ref_sort))}" if st["wrong"] else ""
        add(f"  [要注意] {D.SKILLS[s]} ({s})  {round(score * 100)}%{ws}{hs}{tag}")

    # ③ 根本原因
    roots = sorted(find_roots(weak, watch), key=lambda s: -weak[s])
    conc = area_concentration(wrong)
    add("\n【3】つまずきの根っこ(推定)")
    for s in roots[:3]:
        ds = downstream(s, weak)
        arrow = f" → 連鎖: {', '.join(D.SKILLS[d] for d in ds)}" if ds else ""
        add(f"  ● {D.SKILLS[s]} ({s}) が根っこ{arrow}")
    for p_code, kids in upstream_watch(weak, watch).items():
        add(f"  ● {D.SKILLS[p_code]} ({p_code}) が根っこの可能性（証拠が足りず[要注意]止まり）"
            f" → その先: {', '.join(D.SKILLS[k] for k in kids)}")
    lines.extend(conc)
    if not roots and not conc and not upstream_watch(weak, watch):
        add("  連鎖的な崩れは見られません。誤答したスキルを個別に復習すれば足ります。")

    # ④ 処方
    add("\n【4】復習の処方(この順で)")
    step = 1
    # ★前提が[要注意]止まりでも、weak の親なら処方の先頭に入れる。
    #   ここを weak だけで組むと「平方完成が崩れている生徒に最大最小を処方する」が起きる。
    # ★upstream_watch を無条件で先頭に積むと、[要注意]が3件あるだけで weak の根っこが
    #   処方から全部押し出される(ランダム4000件中 513件=12.8% で発生)。枠は1つまで。
    up = sorted(upstream_watch(weak, watch), key=lambda x: -watch[x][0])[:1]
    targets = (up + [r for r in roots if r not in up])[:3] \
        or sorted(weak, key=lambda x: -weak[x])[:3] \
        or sorted(watch, key=lambda x: -watch[x][0])[:2]
    for s in targets:
        probs = sorted(set(all_probs[s]),
                       key=lambda r: (LEVEL_ORD.get(D.MAP[r]["level"], 1), ref_sort(r)))
        plist = " ".join(r + ("×" if r in wrong else "△" if r in hint
                              else "(未実施)" if r in skip else "") for r in probs)
        add(f"  {step}. 「{D.SKILLS[s]}」を基礎からやり直す: {plist}")
        step += 1
    if wrong:
        head = "最後に誤答全問を解き直し" if step > 1 else "誤答全問を解き直し"
        add(f"  {step}. {head}: {' '.join(sorted(wrong, key=ref_sort))}")
        add("     (日をあけて2回目。2回連続○になったら卒業)")

    # ⑤ 声かけ例
    if targets and wrong:
        add("\n【5】生徒への声かけ例(弱点タグは口にしない)")
        for s in targets[:2]:
            probs = sorted(set(all_probs[s]),
                           key=lambda r: (r not in wrong,
                                          LEVEL_ORD.get(D.MAP[r]["level"], 1), ref_sort(r)))
            if probs:
                add(f"  ・「まず {' と '.join(probs[:2])} をもう一回だけやってみようか」"
                    f"(狙い: {D.SKILLS[s]})")
    add("\n" + "-" * 66)
    add("注: このレポート・診断キー・diagnosis_ia_jaku.py は生徒に渡さない。")
    add("   採点は生徒の自己申告(自己採点シート)でよい。×と△の番号を回収し、△は --hint に渡す。")
    return "\n".join(lines)


def main():
    args = sys.argv[1:]
    name, save, perfect, skip_raw, hint_raw, rest = "", False, False, [], [], []
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("--name", "--skip", "--hint"):
            if i + 1 >= len(args):
                ex = {"--name": "生徒名", "--skip": "A18", "--hint": "A11-2 A11-6"}[a]
                sys.exit(f"エラー: {a} には値が必要です(例: {a} {ex})")
            i += 1
            if a == "--name":
                name = args[i]
            elif a == "--skip":
                skip_raw.append(args[i])
            else:
                hint_raw.append(args[i])
        elif a == "--save":
            save = True
        elif a == "--perfect":
            perfect = True
        elif a in ("-h", "--help"):
            print(__doc__)
            return
        elif a.startswith("--"):
            sys.exit(f"エラー: 知らないオプションです: {a}\n"
                     "  使えるのは --name / --skip / --hint / --save / --perfect / --help")
        else:
            rest.append(a)
        i += 1

    validate_against_content()
    try:
        wrong = set(parse_refs(rest))
        skip = set(parse_refs(skip_raw, expand_units=True))
        hint = set(parse_refs(hint_raw))
    except ValueError as e:
        sys.exit(f"エラー: {e}")

    bad = [r for r in sorted(wrong | skip | hint, key=ref_sort) if r not in D.MAP]
    if bad:
        ranges = ", ".join(f"{u['code']}:1-{u['count']}" for u in D.UNITS_INFO)
        sys.exit(f"エラー: 存在しない番号 {', '.join(bad)}\n有効範囲: {ranges}")
    for a_set, b_set, msg in ((wrong, skip, "--skip と誤答"), (wrong, hint, "×と△"),
                              (hint, skip, "△と--skip")):
        if a_set & b_set:
            sys.exit(f"エラー: {msg} の両方に指定: {', '.join(sorted(a_set & b_set, key=ref_sort))}")
    if len(skip) >= len(D.MAP):
        sys.exit("エラー: 全問が未実施(--skip)指定です。実施した分だけ残してください。")
    if not wrong and not hint and not skip:
        # ★番号を貼り忘れて実行すると「全問正解です」と満点レポートが出てしまう。
        #   本当に全問正解なら --perfect を明示させる(貼り忘れと区別できるように)。
        if not perfect:
            sys.exit("エラー: ×も△も--skipも指定されていません。\n"
                     "  番号を貼り忘れていませんか(例: python3 analyze_ia_jaku.py A06-3 A07-1)。\n"
                     "  本当に全問正解なら --perfect を付けてください。")

    report = build_report(name, wrong, skip, skill_stats(wrong, skip, hint), hint)
    print(report)

    if save:
        today = datetime.date.today().strftime("%Y%m%d")
        path = os.path.expanduser(f"~/Desktop/弱点分析_数学IA_{name or '無記名'}_{today}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(report + "\n")
        print(f"\nSAVED: {path}")


if __name__ == "__main__":
    main()
