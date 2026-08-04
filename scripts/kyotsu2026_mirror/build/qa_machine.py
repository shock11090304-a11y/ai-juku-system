#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""機械QA: 配点合計 / マーク番号連続性 / スロット整合 / 正解位置分布 /
PDFグリフ監査 / 国語コンテンツ欠落(sheet overflow)チェック。"""
import importlib.util, json, os, re, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CONTENT = os.path.join(ROOT, "content")
OUTDIR = os.path.expanduser("~/Desktop/共通テスト2026類似問題")
KAT = re.compile(r"[ア-ン]")
SLOT = re.compile(r"[〔〚]([ア-ン]+)[〕〛]")
CIRC = "①②③④⑤⑥⑦⑧⑨⓪"

issues = []


def load(subject):
    if CONTENT not in sys.path:
        sys.path.insert(0, CONTENT)
    p = os.path.join(CONTENT, subject + ".py")
    spec = importlib.util.spec_from_file_location("m_" + subject, p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.PROB, m.ANS


def texts_of(obj):
    """dict/list を再帰して text/tex/stem/choices 等の文字列を集める"""
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("svg", "html"):
                continue
            out.extend(texts_of(v))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(texts_of(v))
    elif isinstance(obj, str):
        out.append(obj)
    return out


def slot_letters(sec):
    """問題文に現れるスロット文字集合"""
    letters = []
    for s in texts_of(sec):
        for m in SLOT.finditer(s):
            letters.extend(list(m.group(1)))
        # $..$ 内のカタカナ
        for tex in re.findall(r"\$([^$]+)\$", s):
            letters.extend(KAT.findall(tex))
    for b in _blocks(sec):
        if b.get("t") == "m":
            letters.extend(KAT.findall(b["tex"]))
    return letters


def _blocks(sec):
    for part in sec.get("parts", []):
        yield from part.get("blocks", [])
    yield from sec.get("units", [])


def check_math(subject):
    prob, ans = load(subject)
    print(f"\n=== {subject} ===")
    total = sum(s["points"] for s in prob["sections"])
    print("大問配点列:", [(s['no'], s['points']) for s in prob['sections']], "合計", total)
    if subject == "math1a" and total != 100:
        issues.append(f"{subject}: 配点合計 {total} != 100")
    if subject == "math2bc":
        # optional に「選択」を含む大問のみ選択問題扱い(必答問題badgeは必答)
        req = sum(s["points"] for s in prob["sections"] if "選択" not in str(s.get("optional") or ""))
        opt = [s for s in prob["sections"] if "選択" in str(s.get("optional") or "")]
        pick = opt[0]["points"] if opt else 16
        if req + 3 * pick != 100:
            issues.append(f"{subject}: 必答{req}+選択{3*pick} != 100")
    sel_counter = Counter()
    for sec, asec in zip(prob["sections"], ans["sections"]):
        want = slot_letters(sec)
        have = list(asec.get("slots", {}).keys())
        # 問題側の初出順ユニーク列
        seen, uw = set(), []
        for c in want:
            if c not in seen:
                seen.add(c)
                uw.append(c)
        only_p = [c for c in uw if c not in have]
        only_a = [c for c in have if c not in uw]
        if only_p or only_a:
            issues.append(f"{subject} 第{sec['no']}問: スロット欠落/余分 問題のみ{only_p} 解答のみ{only_a}")
        elif uw != have:
            # 集合は一致・順序のみ相違(解答表は五十音順で正常) → 情報表示のみ
            print(f"  [info] 第{sec['no']}問: スロット登場順{''.join(uw)} / 解答表順{''.join(have)}")
        for k, v in asec.get("slots", {}).items():
            if v in CIRC:
                sel_counter[v] += 1
            elif not re.fullmatch(r"[0-9−\-]", str(v)):
                issues.append(f"{subject} 第{sec['no']}問 {k}: 不正な値 {v!r}")
    print("選択式スロットの正解分布:", dict(sel_counter))


def check_choicesubj(subject, expect_total, expect_marks):
    prob, ans = load(subject)
    print(f"\n=== {subject} ===")
    # マーク番号と選択肢数の対応表を問題側から作る
    qmap = {}
    for sec in prob["sections"]:
        for b in _blocks(sec):
            if b.get("t") == "q" and b.get("no") is not None:
                qmap[b["no"]] = len(b.get("choices", []) or [])
    total = 0
    marks = []
    pos_counter = Counter()

    def parse_pts(v):
        """完答型の '3*' や '＊' を許容: 先頭の整数を配点、記号のみは0(グループ配点は先頭マークに集約)。"""
        m = re.match(r"\s*(\d+)", str(v))
        return int(m.group(1)) if m else 0

    for asec in ans["sections"]:
        sec_pts = 0
        for a in asec.get("answers", []):
            marks.append(a["qno"])
            sec_pts += parse_pts(a["points"])
            ansstr = str(a["answer"])
            nch = qmap.get(a["qno"], 0)
            for ch in ansstr:
                if ch in CIRC:
                    pos_counter[ch] += 1
                    idx = CIRC.index(ch) + 1 if ch != "⓪" else 0
                    if nch and idx > nch:
                        issues.append(f"{subject} 問{a['qno']}: 正解{ch}が選択肢数{nch}を超過")
        if asec.get("points") and sec_pts != asec["points"]:
            issues.append(f"{subject} 第{asec['section']}問: 小問配点合計{sec_pts} != {asec['points']}")
        total += sec_pts
    if total != expect_total:
        issues.append(f"{subject}: 配点合計 {total} != {expect_total}")
    dup = [m for m, c in Counter(marks).items() if c > 1]
    uniq = sorted(set(marks))
    if uniq != list(range(1, expect_marks + 1)):
        missing = sorted(set(range(1, expect_marks + 1)) - set(uniq))
        extra = sorted(set(uniq) - set(range(1, expect_marks + 1)))
        issues.append(f"{subject}: マーク番号 欠番{missing} 余分{extra} 重複{dup}")
    # 正解位置の偏り・連続の検査(単一選択のみ・マーク番号順)
    single = []
    amap = {}
    for asec in ans["sections"]:
        for a in asec.get("answers", []):
            amap[a["qno"]] = str(a["answer"])
    for q in sorted(amap):
        s = amap[q]
        if len(s) == 1 and s in CIRC:  # 単一選択(順不同・完答連結は除外)
            single.append(s)
    # 最大連続
    run, mx, mxch = 1, 1, single[0] if single else ""
    for i in range(1, len(single)):
        run = run + 1 if single[i] == single[i-1] else 1
        if run > mx:
            mx, mxch = run, single[i]
    if mx >= 4:
        issues.append(f"{subject}: 正解が同一番号{mxch}で{mx}連続(3以下に散らすこと)")
    # 偏り(最頻値が単一選択数の45%超)
    if single:
        c = Counter(single)
        top, topn = c.most_common(1)[0]
        if topn / len(single) > 0.45:
            issues.append(f"{subject}: 正解位置が{top}に偏り({topn}/{len(single)}={topn/len(single)*100:.0f}%)")
    print(f"配点合計 {total} / マーク番号 1〜{max(marks) if marks else 0} / 正解分布 {dict(sorted(pos_counter.items()))} / 単一選択最大連続{mx}")


def check_pdf_glyphs():
    import fitz
    print("\n=== PDFグリフ監査 ===")
    for fn in sorted(os.listdir(OUTDIR)):
        if not fn.endswith(".pdf") or fn.startswith("_"):
            continue
        d = fitz.open(os.path.join(OUTDIR, fn))
        bad = 0
        chars = 0
        for pg in d:
            t = pg.get_text()
            chars += len(t)
            bad += t.count("�") + sum(1 for c in t if ord(c) < 9 and c not in "\n\t")
        print(f"{fn}: pages={len(d)} chars={chars} bad={bad}")
        if bad:
            issues.append(f"{fn}: 不正グリフ {bad}")
        d.close()


def check_kokugo_coverage():
    """縦書きsheetのoverflow欠落検知: 本文各段落の先頭/末尾20字がPDFテキストに存在するか"""
    import fitz
    print("\n=== 国語 コンテンツ欠落チェック ===")
    prob, _ = load("kokugo")
    pdf = os.path.join(OUTDIR, f'{prob["meta"]["outname"]}_問題編.pdf')
    if not os.path.exists(pdf):
        issues.append("kokugo: 問題編PDFが無い")
        return
    d = fitz.open(pdf)
    full = "".join(pg.get_text() for pg in d).replace("\n", "")
    d.close()
    def norm(s):
        s = s.replace("{Q}", "")                # 解答番号ボックスのテンプレ記号
        s = re.sub(r"<rt>.*?</rt>", "", s)      # ルビの読みを除去(縦書き抽出で位置が動くため)
        s = re.sub(r"<[^>]+>", "", s)           # 残りのタグ除去
        s = re.sub(r"（注[0-9]+）|〔[^〕]*〕|〚[^〛]*〛", "", s)  # 注参照・スロットを除去
        return re.sub(r"\s", "", s)
    full_n = norm(full)
    # ルビ読み・解答番号ボックス番号が抽出テキストに割り込むため、断片の部分一致は
    # 偽陰性が多い。よって「本文ユニットが丸ごと消えていないか(=どの断片も一切
    # 見つからない)」だけを検査する。縦書き overflow:hidden での大規模クリップ検出用。
    miss = 0
    for sec in prob["sections"]:
        for u in sec.get("units", []):
            src = None
            if u.get("t") in ("para", "lead") and isinstance(u.get("text"), str):
                src = u["text"]
            elif u.get("t") == "q":
                src = u.get("stem")
            if not src:
                continue
            t = norm(src)
            if len(t) < 16:
                continue
            frags = [t[:10], t[len(t)//3:len(t)//3+10], t[2*len(t)//3:2*len(t)//3+10], t[-10:]]
            if not any(f and f in full_n for f in frags):
                miss += 1
                issues.append(f"kokugo 第{sec['no']}問: ユニット丸ごと欠落の疑い「{t[:24]}…」")
    print("欠落ユニット(丸ごと消失):", miss)


def _guard(label, fn, *a):
    try:
        fn(*a)
    except Exception as e:
        import traceback
        issues.append(f"{label}: QA実行中に例外 {type(e).__name__}: {e}")
        print(f"[SKIP] {label}: {type(e).__name__}: {e}")


def main():
    args = sys.argv[1:] or ["content", "pdf"]
    if "content" in args:
        for s in ("math1a", "math2bc"):
            if os.path.exists(os.path.join(CONTENT, s + ".py")):
                _guard(s, check_math, s)
        if os.path.exists(os.path.join(CONTENT, "english.py")):
            _guard("english", check_choicesubj, "english", 100, 44)
        if os.path.exists(os.path.join(CONTENT, "kokugo.py")):
            _guard("kokugo", check_choicesubj, "kokugo", 200, 37)
    if "pdf" in args:
        _guard("pdf-glyphs", check_pdf_glyphs)
        _guard("kokugo-coverage", check_kokugo_coverage)
    print("\n================")
    if issues:
        print(f"ISSUES ({len(issues)}):")
        for i in issues:
            print(" -", i)
        sys.exit(1)
    print("ALL CLEAN")


if __name__ == "__main__":
    main()
