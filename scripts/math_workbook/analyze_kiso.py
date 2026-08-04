#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数列・確率・ベクトル 基礎徹底問題集 の【塾長用】弱点分析CLI。

生徒の×だった問題番号(印刷版の「単元番号-問題番号」)を入れると、
どのスキルが弱いか・つまずきの根っこはどこか・何を復習させるかを出力する。
★出力レポートと diagnosis_kiso.py は生徒に見せない。

使い方:
  python3 analyze_kiso.py 07-1 07-4 08-6
  python3 analyze_kiso.py --name 山田太郎 --save 03-9 03-12 04-1 01-6
  python3 analyze_kiso.py --hint "10-1 10-7" 04-3    # △(公式を見て正解)も渡す
  python3 analyze_kiso.py --skip 12 07-9 10-4        # 単元12まるごと未実施
  python3 analyze_kiso.py --skip "12-9 12-10" 10-4   # 問題単位の未実施
番号は 7-3 / 07-3 / 全角 / カンマ区切り すべてOK。--skip に単元番号だけ渡すと単元全体を除外。
"""
import sys, os, re, datetime, unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import diagnosis_kiso as D
import diagnosis_kiso2 as D2   # 第2集(単元13〜24)


class _Merged:
    """第1集(単元01〜12)と第2集(単元13〜24)を1つの診断空間として扱う。
    ★単元番号が重ならないので「05-7」がどちらの集かは一意に決まる(誤診断が原理的に起きない)。"""
    SKILLS = D.SKILLS
    PREREQ = D.PREREQ
    LEVEL_W = D.LEVEL_W
    ROLE_W = D.ROLE_W
    UNITS_INFO = D.UNITS_INFO + D2.UNITS_INFO
    MAP = {**D.MAP, **D2.MAP}


_D1, _D2 = D, D2
D = _Merged
BOOK_OF = {**{u["idx"]: "第1集" for u in _D1.UNITS_INFO},
           **{u["idx"]: "第2集" for u in _D2.UNITS_INFO}}

WEAK_TH, WATCH_TH = 0.5, 0.25
MIN_WEAK_WRONG = 2          # 弱点断定には誤答2問以上の証拠を要求(1問なら「要再測」)
LEVEL_JA = {"basic": "基礎", "standard": "標準", "advanced": "発展"}
LEVEL_ORD = {"basic": 0, "standard": 1, "advanced": 2}
PARTS_DEF = [("確率", range(1, 5)), ("数列", range(5, 9)), ("ベクトル", range(9, 13)),
             ("確率", range(13, 17)), ("数列", range(17, 23)),
             ("Σと和", range(23, 25)), ("ベクトル", range(25, 28))]

Z2H = str.maketrans("０１２３４５６７８９－ー−‐―〜、，", "0123456789------,,")


def unit_size(ui):
    return next(u["count"] for u in D.UNITS_INFO if u["idx"] == ui)


def parse_refs(tokens, expand_units=False):
    """'07-3' '7-3' '７−３' 'A,B' 混在を (単元,番号) タプルのlistへ。
    expand_units=True なら「12」だけの指定を単元12の全問に展開(--skip用)。"""
    refs = []
    for tk in tokens:
        for piece in tk.translate(Z2H).replace(",", " ").split():
            m = re.fullmatch(r"(\d{1,2})-(\d{1,2})", piece)
            if m:
                refs.append((int(m.group(1)), int(m.group(2))))
                continue
            m = re.fullmatch(r"(\d{1,2})", piece)
            if m and expand_units:
                ui = int(m.group(1))
                if not any(u["idx"] == ui for u in D.UNITS_INFO):
                    ids = [u["idx"] for u in D.UNITS_INFO]
                    raise ValueError(f"単元 {ui} は存在しません({min(ids):02d}〜{max(ids):02d})")
                refs.extend((ui, j) for j in range(1, unit_size(ui) + 1))
                continue
            hint = "。単元まるごとは --skip 12 のように単元番号だけでも指定できます" if not expand_units else ""
            raise ValueError(f"番号の形式が不正です: 「{piece}」(例: 7-3 または 07-3){hint}")
    return refs


def _numbered(mod, offset):
    """content モジュールを build と同じ規則で採番して {キー: 問題} にする。"""
    units = [u for p in mod.PARTS for u in p["units"]]
    for u in units:
        order, buckets = [], {}
        for q in u["problems"]:
            g = q.get("group", "")
            if g not in buckets:
                buckets[g] = []
                order.append(g)
            buckets[g].append(q)
        u["problems"] = [q for g in order for q in buckets[g]]
    out = {}
    for ui, u in enumerate(units, 1 + offset):
        for j, q in enumerate(u["problems"], 1):
            out[f"{ui}-{j}"] = q
    return out


def validate_against_content():
    """content と診断マップのドリフト検知(両集)。印刷版とデータ版のズレを許さない。"""
    import content_kiso as C1
    import content_kiso2 as C2
    problems = {**_numbered(C1, 0), **_numbered(C2, 12)}
    if set(problems.keys()) != set(D.MAP.keys()):
        miss = sorted(set(problems) ^ set(D.MAP))[:6]
        sys.exit(f"★診断マップと問題集がズレています(問題の増減: {miss})。"
                 "diagnosis_kiso.py / diagnosis_kiso2.py を再生成してください。")
    for key, q in problems.items():
        m = D.MAP[key]
        if (q["stem"][:len(m["head"])] != m["head"] or q.get("level", "") != m["level"]
                or q.get("group", "") != m["group"]):
            book = "diagnosis_kiso2.py" if int(key.split("-")[0]) > 12 else "diagnosis_kiso.py"
            sys.exit(f"★診断マップと問題集がズレています({key} の本文/レベル/グループ不一致)。{book} を再生成してください。")


def skill_probs_all():
    """スキル → 担当する全問題ref(primary+sub、skip除外なし)。処方リスト用。"""
    out = {sname: [] for sname in D.SKILLS}
    for key, m in D.MAP.items():
        ref = tuple(int(v) for v in key.split("-"))
        out[m["skill"]].append(ref)
        for c in m["sub"]:
            out[c].append(ref)
    return out


HINT_W = 0.5   # △(公式を見て解けた)は「半分できていない」として数える


def skill_stats(wrong, skip, books=None, hint=frozenset()):
    """スキルごとに (誤答重み, 全体重み, 誤答ref) を集計。skipは分子分母とも除外。
    books を渡すと、その集の問題だけを分母に入れる。hint(△)は重み HINT_W の誤答扱い。"""
    stats = {sname: {"m": 0.0, "t": 0.0, "wrong": [], "hint": []} for sname in D.SKILLS}
    for key, m in D.MAP.items():
        ref = tuple(int(v) for v in key.split("-"))
        if ref in skip:
            continue
        if books and BOOK_OF[ref[0]] not in books:
            continue
        lw = D.LEVEL_W.get(m["level"], 1.0)
        for role, code in [("primary", m["skill"])] + [("sub", c) for c in m["sub"]]:
            w = D.ROLE_W[role] * lw
            stats[code]["t"] += w
            if ref in wrong:
                stats[code]["m"] += w
                stats[code]["wrong"].append(ref)
            elif ref in hint:
                stats[code]["m"] += w * HINT_W
                stats[code]["hint"].append(ref)
    for st in stats.values():
        st["score"] = st["m"] / st["t"] if st["t"] > 0 else 0.0
    return stats


def classify(stats):
    """弱点(証拠2問以上) / 要注意(1問のみの高スコア含む) に分類。"""
    weak, watch = {}, {}
    for sname, st in stats.items():
        if not st["wrong"] and not st.get("hint"):
            continue
        ev = len(st["wrong"]) + len(st.get("hint", []))
        if st["score"] >= WEAK_TH and ev >= MIN_WEAK_WRONG:
            weak[sname] = st["score"]
        elif st["score"] >= WEAK_TH:
            watch[sname] = (st["score"], "誤答1問のみ・要再測")
        elif st["score"] >= WATCH_TH:
            watch[sname] = (st["score"], "")
    return weak, watch


def find_roots(weak):
    """弱いスキルのうち、前提スキルがどれも弱くないもの=根っこ。"""
    return [sname for sname in weak if not any(p in weak for p in D.PREREQ.get(sname, []))]


def downstream(root, weak):
    """root を前提に持つ(推移的)弱スキル=連鎖して崩れている先。"""
    out, frontier = set(), {root}
    while frontier:
        nxt = set()
        for sname in weak:
            if sname in out or sname in frontier:
                continue
            if any(p in frontier or p in out for p in D.PREREQ.get(sname, [])):
                nxt.add(sname)
        out |= nxt
        frontier = nxt
    return sorted(out, key=lambda sname: -weak[sname])


def part_concentration(wrong):
    """編(確率/数列/ベクトル)単位の「広く浅い崩れ」検出。
    誤答の2/3以上が同一編・4問以上・3単元以上に分散 → 編まるごと再点検を勧める。"""
    notes = []
    for pname, rng in PARTS_DEF:
        pw = [r for r in wrong if r[0] in rng]
        punits = {r[0] for r in pw}
        if len(pw) >= 4 and len(pw) * 3 >= len(wrong) * 2 and len(punits) >= 3:
            notes.append(f"  ● {pname}分野全体に誤答が分散({len(pw)}問・{len(punits)}単元) "
                         f"→ 単元を絞らず{pname}編を頭から基礎再点検")
    return notes


def fmt_ref(ref):
    return f"{ref[0]:02d}-{ref[1]}"


def pad_ja(s, width):
    w = sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in s)
    return s + " " * max(0, width - w)


def build_report(name, wrong, skip, stats, hint=frozenset()):
    unit_name = {u["idx"]: u["name"] for u in D.UNITS_INFO}
    all_probs = skill_probs_all()
    touched_books = {BOOK_OF[r[0]] for r in (wrong | skip | hint)} or {"第1集"}
    in_scope = {k for k in D.MAP if BOOK_OF[int(k.split("-")[0])] in touched_books}
    total = len(in_scope) - len(skip)
    lines = []
    add = lines.append
    today = datetime.date.today().strftime("%Y-%m-%d")
    add("=" * 62)
    add(f"◆ 弱点分析レポート【塾長用・生徒非公開】  {today}")
    add(f"  生徒: {name or '(無記名)'}   教材: 数列・確率・ベクトル 基礎徹底問題集")
    add(f"  誤答 {len(wrong)}問 / 出題 {total}問 (正答率 {round(100 * (total - len(wrong)) / total)}%)"
        + (f"   △{len(hint)}問(公式を見て正解=自力ではない・重み{HINT_W}で誤答に算入)" if hint else "")
        + (f"   未実施 {len(skip)}問は除外" if skip else ""))
    add("=" * 62)

    # ① 単元別(実施した集だけ表示)
    add("\n【1】単元別の成績")
    touched = {r[0] for r in wrong} | {r[0] for r in skip} | {r[0] for r in hint}
    books = [b for b in ("第1集", "第2集")
             if any(BOOK_OF[u["idx"]] == b for u in D.UNITS_INFO)]
    for book in books:
        idxs = [u["idx"] for u in D.UNITS_INFO if BOOK_OF[u["idx"]] == book]
        # 実施の形跡が無い集は丸ごと省く(第1集だけ解いた回で第2集が全部○に見えるのを防ぐ)
        if not (touched & set(idxs)):
            continue
        if len(books) > 1:
            add(f"  《{book}》")
        for ui in idxs:
            refs = [r for r in sorted(wrong) if r[0] == ui]
            cnt = unit_size(ui) - sum(1 for r in skip if r[0] == ui)
            if cnt == 0:
                add(f"    {ui:02d} {pad_ja(unit_name[ui], 24)}(未実施)")
                continue
            hrefs = [r for r in sorted(hint) if r[0] == ui]
            load = len(refs) + HINT_W * len(hrefs)
            mark = "★" if load / cnt >= 0.4 else (" " if not refs and not hrefs else "・")
            add(f"  {mark} {ui:02d} {pad_ja(unit_name[ui], 24)}誤答 {len(refs)}/{cnt}"
                + (f"（△{len(hrefs)}）" if hrefs else "")
                + (f"   [{' '.join(fmt_ref(r) for r in refs)}]" if refs else "")
                + (f"  △[{' '.join(fmt_ref(r) for r in hrefs)}]" if hrefs else ""))

    # ② スキル判定
    weak, watch = classify(stats)
    add("\n【2】弱点スキル(裏タグ集計・生徒には見せない)")
    if not wrong and not hint:
        add("  全問正解です。この教材の範囲に弱点はありません。")
    elif not wrong:
        add("  ×はありませんが、△(公式を見て解けた)が残っています。下の項目は自力で解けるまで詰めましょう。")
    elif not weak and not watch:
        add("  弱点と言えるスキルはありません。誤答は単発ミスの範囲です。")
    for sname in sorted(weak, key=lambda x: -weak[x]):
        st = stats[sname]
        chain = [p for p in D.PREREQ.get(sname, []) if p in weak]
        tag = f" ← 根っこは「{'・'.join(D.SKILLS[p] for p in chain)}」の連鎖" if chain else ""
        hs = f"  △: {' '.join(fmt_ref(r) for r in sorted(st.get('hint', [])))}" if st.get("hint") else ""
        add(f"  [弱点] {D.SKILLS[sname]} ({sname})  {round(st['score'] * 100)}%"
            f"  誤答: {' '.join(fmt_ref(r) for r in sorted(st['wrong']))}{hs}{tag}")
    for sname in sorted(watch, key=lambda x: -watch[x][0]):
        st = stats[sname]
        score, note = watch[sname]
        tag = f" ({note})" if note else ""
        hs = f"  △: {' '.join(fmt_ref(r) for r in sorted(st.get('hint', [])))}" if st.get("hint") else ""
        add(f"  [要注意] {D.SKILLS[sname]} ({sname})  {round(score * 100)}%"
            f"  誤答: {' '.join(fmt_ref(r) for r in sorted(st['wrong']))}{hs}{tag}")

    # ③ 根本原因(スキル連鎖 + 編単位の分散)
    roots = sorted(find_roots(weak), key=lambda sname: -weak[sname])
    conc = part_concentration(wrong)
    add("\n【3】つまずきの根っこ(推定)")
    for sname in roots[:3]:
        ds = downstream(sname, weak)
        arrow = f" → 連鎖: {', '.join(D.SKILLS[d] for d in ds)}" if ds else ""
        add(f"  ● {D.SKILLS[sname]} ({sname}) が根っこ{arrow}")
    lines.extend(conc)
    if not roots and not conc:
        add("  連鎖的な崩れは見られません。誤答したスキルを個別に復習すれば足ります。")

    # ④ 処方(未実施も含めた全担当問題から組む)
    add("\n【4】復習の処方(この順で)")
    step = 1
    targets = roots[:3] or sorted(weak, key=lambda x: -weak[x])[:3] \
        or [sname for sname in sorted(watch, key=lambda x: -watch[x][0])[:2]]
    for sname in targets:
        probs = sorted(set(all_probs[sname]),
                       key=lambda r: (LEVEL_ORD.get(D.MAP[f"{r[0]}-{r[1]}"]["level"], 1), r))
        plist = " ".join(
            fmt_ref(r) + ("×" if r in wrong else "(未実施)" if r in skip else "")
            for r in probs)
        add(f"  {step}. 「{D.SKILLS[sname]}」を基礎からやり直す: {plist}")
        step += 1
    if wrong:
        head = "最後に誤答全問を解き直し" if step > 1 else "誤答全問を解き直し"
        add(f"  {step}. {head}: {' '.join(fmt_ref(r) for r in sorted(wrong))}")
        add("     (日をあけて2回目。2回連続○になったら卒業)")

    # ⑤ 声かけ例(誤答した問題を優先して指名)
    if targets and wrong:
        add("\n【5】生徒への声かけ例(弱点タグは口にしない)")
        for sname in targets[:2]:
            probs = sorted(set(all_probs[sname]),
                           key=lambda r: (r not in wrong,
                                          LEVEL_ORD.get(D.MAP[f"{r[0]}-{r[1]}"]["level"], 1), r))
            if not probs:
                continue
            add(f"  ・「まず {' と '.join(fmt_ref(r) for r in probs[:2])} をもう一回だけやってみようか」"
                f"(狙い: {D.SKILLS[sname]})")
    add("\n" + "-" * 62)
    add("注: このレポート・診断キー・diagnosis_kiso.py は生徒に渡さない。")
    add("   採点は生徒の自己申告(自己採点シート)でよい。×と△の番号を回収し、△は --hint に渡す。")
    return "\n".join(lines)


def main():
    args = sys.argv[1:]
    name, save, skip_raw, hint_raw = "", False, [], []
    rest = []
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("--name", "--skip", "--hint"):
            if i + 1 >= len(args):
                ex = {"--name": "生徒名", "--skip": "12", "--hint": "10-1 10-7"}[a]
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
        elif a in ("-h", "--help"):
            print(__doc__)
            return
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

    bad = [r for r in sorted(wrong | skip | hint) if f"{r[0]}-{r[1]}" not in D.MAP]
    if bad:
        ranges = ", ".join(f"{u['idx']:02d}:1-{u['count']}" for u in D.UNITS_INFO)
        sys.exit(f"エラー: 存在しない番号 {', '.join(fmt_ref(r) for r in bad)}\n有効範囲: {ranges}")
    if wrong & skip:
        sys.exit(f"エラー: --skip と誤答の両方に指定: {', '.join(fmt_ref(r) for r in sorted(wrong & skip))}")
    if wrong & hint:
        sys.exit(f"エラー: ×と△の両方に指定: {', '.join(fmt_ref(r) for r in sorted(wrong & hint))}")
    if hint & skip:
        sys.exit(f"エラー: △と--skipの両方に指定: {', '.join(fmt_ref(r) for r in sorted(hint & skip))}")
    if len(skip) >= len(D.MAP):
        sys.exit("エラー: 全問が未実施(--skip)指定です。実施した分だけ残してください。")

    books = {BOOK_OF[r[0]] for r in (wrong | skip | hint)} or {"第1集"}
    stats = skill_stats(wrong, skip, books, hint)
    report = build_report(name, wrong, skip, stats, hint)
    print(report)

    if save:
        today = datetime.date.today().strftime("%Y%m%d")
        path = os.path.expanduser(f"~/Desktop/弱点分析_{name or '無記名'}_{today}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(report + "\n")
        print(f"\nSAVED: {path}")


if __name__ == "__main__":
    main()
