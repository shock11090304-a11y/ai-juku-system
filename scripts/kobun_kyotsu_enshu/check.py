# -*- coding: utf-8 -*-
"""第4問（古文）演習問題集の決定的検査
   解答番号・配点・選択肢・傍線記号・注・現代語訳の対応・レベルの階段・正解の分布。
   引数で刷ったPDFを渡すと、データの全要素がPDFに出ているかも照合する。

     python3 check.py                       # データだけ検査（CIはこれ）
     python3 check.py <問題編.pdf> <解答解説編.pdf>
"""
import json, re, sys, os, glob, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build import LEVELS, body_chars   # レベルの定義と字数の数え方はビルダーが正典

CIRC = "①②③④⑤"
bad = []
def ng(m): bad.append(m); print("NG " + m)

def plain(s): return re.sub(r"\{\{/?[abcwxy]\}\}", "", s)

def pdf_text(path):
    """PDFの全文を、フッター行と傍線記号を除いて連結する（ページ跨ぎの文を照合できるように）"""
    import fitz
    d = fitz.open(path)
    out = []
    for pg in d:
        t = pg.get_text()
        t = re.sub(r"TRILLION\s*AI\s*学習塾[\s\S]*$", "", t)   # フッターは縦組みでも末尾にまとめて出る
        t = re.sub(r"\n\s*\d+\s*/\s*\d+\s*\n?", "\n", t)
        out.append(t)
    t = "".join(out)
    return re.sub(r"[0-9]", "", re.sub(r"\s", "", t))

def check_glyphs(path, label):
    """刷り上がりに、出てはいけない文字が出ていないか（豆腐・制御文字・タグやMarkdownの露出）"""
    import fitz
    d = fitz.open(path)
    t = "".join(p.get_text() for p in d)
    ctrl = "".join(chr(c) for c in list(range(0, 9)) + [11, 12] + list(range(14, 32)))
    if t.count("\ufffd"): ng(f"{label}: 字形の出ない文字（豆腐）が {t.count(chr(0xfffd))} 個")
    ctrls = sorted({hex(ord(c)) for c in t if c in ctrl})
    if ctrls: ng(f"{label}: 制御文字が出ている {ctrls}")
    tags = re.findall(r"<[a-zA-Z/][^>]{0,20}>", t)
    if tags: ng(f"{label}: HTMLのタグがそのまま出ている {tags[:3]}")
    if "**" in t: ng(f"{label}: Markdownの強調記号がそのまま出ている")
    for i, p in enumerate(d):
        if not [b for b in p.get_text("blocks") if b[4].strip()]:
            ng(f"{label}: {i+1}ページが空白")
    print(f"   {label}: {len(d)}ページ／{len(t)}字（豆腐・制御文字・タグ露出なし）")

def check_layout(path, label, skip_pages=2):
    """版面の欠陥。★「肢が1つだけ次ページに残る」「傍線の罫だけが余白に取り残される」は
       文字を照合するだけの検査では絶対に見えない（どちらも実際に起きた）。"""
    import fitz
    d = fitz.open(path)
    for i, p in enumerate(d, 1):
        if i <= skip_pages: continue          # 巻頭は手順の①〜⑥なので選択肢ではない
        lines = [l.strip() for l in p.get_text().split("\n") if l.strip()]
        c1 = sum(1 for l in lines if l.startswith("①"))
        c5 = sum(1 for l in lines if l.startswith("⑤"))
        if c1 != c5:
            ng(f"{label} {i}ページ: 選択肢のかたまりがページをまたいでいる（①が{c1}個・⑤が{c5}個）")
        # 傍線（縦組みなので縦の線）は、必ずそのすぐ隣に本文がある。
        # 本文の無い所に残った線＝改ページで装飾だけ取り残された罫（実際に起きた）。
        segs, hori = [], []
        for dr in p.get_drawings():
            for it in dr["items"]:
                if it[0] == "l":
                    a, b2 = it[1], it[2]
                    if abs(a.x - b2.x) < 1.5 and abs(a.y - b2.y) > 8:
                        segs.append((a.x, min(a.y, b2.y), max(a.y, b2.y)))
                    elif abs(a.y - b2.y) < 1.5 and abs(a.x - b2.x) > 4:
                        hori.append((a.y, min(a.x, b2.x), max(a.x, b2.x)))
                elif it[0] == "re":
                    r = it[1]
                    if r.width < 3 and r.height > 8: segs.append((r.x0, r.y0, r.y1))
                    elif r.height < 3 and r.width > 4: hori.append((r.y0, r.x0, r.x1))
                    elif r.width > 4 and r.height > 8:      # 枠（表・囲み）は縦横そろって出る
                        hori += [(r.y0, r.x0, r.x1), (r.y1, r.x0, r.x1)]
        # ★表や囲みの罫は、縦線の端に横線が接している。傍線にはそれが無い。
        segs = [s for s in segs
                if not any(abs(h[0] - s[1]) < 2.5 or abs(h[0] - s[2]) < 2.5
                           for h in hori if h[1] - 2 <= s[0] <= h[2] + 2)]
        words = p.get_text("words")
        stray = []
        for x, y0, y1 in segs:
            near = [w for w in words if abs((w[0] + w[2]) / 2 - x) < 16 and w[3] > y0 and w[1] < y1]
            if not near: stray.append(round(x, 1))
        if stray:
            ng(f"{label} {i}ページ: 本文の無い所に縦線が{len(stray)}本（傍線だけが取り残されている）x={stray[:4]}")
    print(f"   {label}: 版面の欠陥なし（選択肢の分断・取り残された罫）")

def check_pdf(sets, qpdf, apdf):
    """データの全要素が、刷り上がりに出ているかを逆向きに照合する"""
    qt, at = pdf_text(qpdf), pdf_text(apdf)
    base = lambda x: re.sub(r"[0-9]", "", re.sub(r"\s", "", x))
    st = base                                                    # 設問文・選択肢・解説はそのまま
    MARK = r"[（(](?:ア|イ|ウ|Ａ|Ｂ|A|B)[)）]"                       # 本文は組版時に記号が入るので除く
    stp = lambda x: re.sub(MARK, "", base(x))
    qtp = re.sub(MARK, "", qt)
    for S in sets:
        sid = S["id"]
        for ln in plain(S["passage"]).split("\n"):
            if stp(ln) and stp(ln) not in qtp: ng(f"第{sid}回 本文がPDFにない: {ln[:34]}")
        for q in S["questions"]:
            for ln in q["text"].split("\n"):      # 設問文は改行のたびに段落が分かれて組まれる
                if st(ln) and st(ln) not in qt: ng(f"第{sid}回 問{q['no']} 設問文がPDFにない: {ln[:34]}")
            for it in q["items"]:
                for c in it["choices"]:
                    if not st(c): ng(f"第{sid}回 問{q['no']}{it['label']}: 選択肢が空")
                    elif st(c) not in qt: ng(f"第{sid}回 問{q['no']}{it['label']} 選択肢がPDFにない: {c[:26]}")
            if st(q["exp"]) not in at: ng(f"第{sid}回 問{q['no']} 解説が解答編にない")
            # ★刷り上がりの「正解 ⑤」行が、データの answer（0始まり）と合っているか。
            #   0始まり/1始まりの取り違えはこのリポジトリで何度も起きている。
            want = "正解" + "".join((it["label"] or "") + CIRC[it["answer"]] for it in q["items"])
            if base(want) not in at:
                ng(f"第{sid}回 問{q['no']}: 解答編の「正解」行が合わない（期待 {want}）")
        for n in S["notes"]:
            if st(n["gloss"]) not in qt: ng(f"第{sid}回 注「{n['word']}」がPDFにない")
        for ln in S["translation"].split("\n"):
            if st(ln) and st(ln) not in at: ng(f"第{sid}回 現代語訳が解答編にない: {ln[:28]}")
        for g in S["grammar"]:
            if st(g["point"]) not in at: ng(f"第{sid}回 文法「{g['phrase'][:12]}」が解答編にない")
        for r in S["rules_used"]:
            if st(r["where"]) not in at: ng(f"第{sid}回 ルール「{r['rule'][:12]}」が解答編にない")

def main():
    files = sorted(glob.glob(os.path.join(HERE, "sets", "set*.json")))
    if not files: ng("sets/set*.json が無い")
    # ★原稿・刷るデータ・正解位置表の3つで回がそろっているか。
    #   1つでも欠けると、5回分の冊子がそのまま刷られる（4ゲートとも緑だった）。
    sys.path.insert(0, os.path.join(HERE, "src"))
    import positions
    have = {int(re.search(r"\d+", os.path.basename(f)).group(0)) for f in files}
    drafts = {int(re.search(r"\d+", os.path.basename(f)).group(0))
              for f in glob.glob(os.path.join(HERE, "src", "set*.py"))}
    if have != drafts or have != set(positions.POS):
        ng(f"回が足りない／余っている: 刷るデータ{sorted(have)} 原稿{sorted(drafts)} 正解位置表{sorted(positions.POS)}")
    sets = sorted([json.load(open(f, encoding="utf-8")) for f in files], key=lambda x: x["id"])
    dist = collections.Counter()
    ladder = []
    refs = []
    for S in sets:
        sid = S["id"]
        if S["level_no"] not in LEVELS:
            ng(f"第{sid}回: level_no が {S['level_no']}（1〜3であるべき）"); continue
        # 1) 設問数・解答番号・配点
        if len(S["questions"]) != 5: ng(f"第{sid}回: 設問が{len(S['questions'])}問")
        nums, total = [], 0
        for q in S["questions"]:
            ns = [x.strip() for x in re.split(r"[・,、]", q["nums"]) if x.strip()]
            nums += ns
            if len(ns) != len(q["items"]):
                ng(f"第{sid}回 問{q['no']}: 解答番号{len(ns)}個 ≠ 小問{len(q['items'])}個")
            m = re.search(r"(\d+)", q["points"])
            if not m: ng(f"第{sid}回 問{q['no']}: 配点が読めない「{q['points']}」")
            else: total += int(m.group(1)) * len(q["items"])
            for it in q["items"]:
                if len(it["choices"]) != 5: ng(f"第{sid}回 問{q['no']}{it['label']}: 選択肢が{len(it['choices'])}個")
                if len(set(it["choices"])) != len(it["choices"]): ng(f"第{sid}回 問{q['no']}{it['label']}: 選択肢に重複")
                if not 0 <= it["answer"] < len(it["choices"]): ng(f"第{sid}回 問{q['no']}{it['label']}: 正解番号が範囲外")
                else: dist[CIRC[it["answer"]]] += 1
                if "pos" in it: ng(f"第{sid}回 問{q['no']}{it['label']}: pos が残っている（make_sets を通していない）")
            if not q.get("rules"): ng(f"第{sid}回 問{q['no']}: 参照ルールがない")
            if len(q.get("exp", "")) < 120: ng(f"第{sid}回 問{q['no']}: 解説が{len(q.get('exp',''))}字と短い")
            if "[[" in q.get("exp", ""): ng(f"第{sid}回 問{q['no']}: 解説に未解決の選択肢参照が残っている")
            if re.search(r"[①-⑤]", "".join(c for it in q["items"] for c in it["choices"])):
                ng(f"第{sid}回 問{q['no']}: 選択肢の中に丸数字がある（並べ替えでずれる）")
        if nums != [str(n) for n in range(23, 30)]:
            ng(f"第{sid}回: 解答番号が23〜29の連番でない → {nums}")
        if total != 45: ng(f"第{sid}回: 配点合計が{total}点（45点であるべき）")

        # 2) 傍線・波線の記号
        p = S["passage"]
        for k in ("a", "b", "c", "w"):
            o, c = p.count("{{" + k + "}}"), p.count("{{/" + k + "}}")
            if o != 1 or c != 1: ng(f"第{sid}回 本文: 記号{k}が開き{o}個・閉じ{c}個（各1個であるべき）")
        for k in ("x", "y"):
            if p.count("{{" + k + "}}") != p.count("{{/" + k + "}}") or p.count("{{" + k + "}}") != 1:
                ng(f"第{sid}回 本文: 記号{k}の開閉が不一致")

        # 3) 本文の分量と段落（レベルごとに想定が違う）
        body = plain(p)
        n = body_chars(S["passage"])
        lo, hi = LEVELS[S["level_no"]]["chars"]
        if not lo <= n <= hi:
            ng(f"第{sid}回（{LEVELS[S['level_no']]['name']}）本文: {n}字（{lo}〜{hi}字を想定）")
        marks = len(re.findall(r"[（(]注\d+[)）]", body))
        ladder.append((sid, S["level_no"], n, S["minutes"], n / max(marks, 1)))
        po = [x for x in body.split("\n") if x.strip()]
        tj = [x for x in S["translation"].split("\n") if x.strip()]
        if len(po) != len(tj): ng(f"第{sid}回: 本文{len(po)}段落 ≠ 現代語訳{len(tj)}段落")

        # 4) 注
        if not 10 <= len(S["notes"]) <= 20: ng(f"第{sid}回: 注が{len(S['notes'])}個（10〜20個を想定）")
        inline = [int(x) for x in re.findall(r"\(注(\d+)\)", p)]
        if inline != list(range(1, len(S["notes"]) + 1)):
            ng(f"第{sid}回: 本文の(注n)が1からの連番で注の数と合わない → {inline}")
        flat = re.sub(r"\s", "", re.sub(r"[（(][ぁ-んァ-ン]+[)）]", "", re.sub(r"[（(]注\d+[)）]", "", body)))
        for nt in S["notes"]:
            # ★先頭2字だけの照合では「ありもせぬ語」が素通りする（古文には「あり」が頻出）。
            #   見出し語そのものが本文にあることを求める。
            head = re.sub(r"[「」『』\s]", "", re.sub(r"^\d+\s*", "", nt["word"]))
            if head and head not in flat:
                ng(f"第{sid}回 注: 「{nt['word']}」が本文に見当たらない")

        # 4b) 解説や選択肢が「注n」と書いている箇所が、実在する注を指しているか
        #     ★注を1つ足すと以降の番号がずれる。参照だけ古いまま残る事故を止める。
        blob = "".join(q["exp"] + q["text"] + "".join(c for it in q["items"] for c in it["choices"])
                       for q in S["questions"])
        for m in re.finditer(r"注(\d+)", blob):
            k = int(m.group(1))
            if not 1 <= k <= len(S["notes"]):
                ng(f"第{sid}回: 解説・選択肢が存在しない注{k}を指している（注は{len(S['notes'])}個）")
            else:
                refs.append((sid, k, S["notes"][k - 1]["word"]))

        # 5) 文法・ルール
        if not 8 <= len(S["grammar"]) <= 16: ng(f"第{sid}回: 文法の項目が{len(S['grammar'])}個")
        for g in S["grammar"]:
            if re.sub(r"\s", "", g["phrase"])[:3] not in flat:
                ng(f"第{sid}回 文法: 「{g['phrase']}」が本文に見当たらない")
        seen = set()
        for r in S["rules_used"]:
            if not re.match(r"ルール(0[1-9]|1[0-9]|20)\s", r["rule"]):
                ng(f"第{sid}回: ルール名が規定の形式でない「{r['rule']}」")
            if r["rule"] in seen: ng(f"第{sid}回: ルールが重複「{r['rule'][:12]}」")
            seen.add(r["rule"])
        have = {m.group(0) for x in S["rules_used"] if (m := re.match(r"ルール\d\d", x["rule"]))}
        for q in S["questions"]:
            for t in q["rules"]:
                if t not in have: ng(f"第{sid}回 問{q['no']}: 参照ルール {t} が「使うルール」の表に無い")
        # 6) 典拠
        if not S.get("source_url", "").strip(): ng(f"第{sid}回: 典拠のURLがない")
        if len(S.get("confidence", "")) < 80: ng(f"第{sid}回: 典拠の確からしさの記録が短い")

    # 7) レベルの階段が本当に階段になっているか（基礎のほうが長い、では話が合わない）
    ladder.sort()
    for a, b in zip(ladder, ladder[1:]):
        if b[1] < a[1]: ng(f"第{b[0]}回: レベルが第{a[0]}回より下がっている（前から順に解く並びでない）")
        if b[2] <= a[2]: ng(f"第{b[0]}回: 本文が第{a[0]}回より短い（{a[2]}字→{b[2]}字）")
        # ★階段は「本文が長くなること」ではなく「1分あたりに読む量が増えること」で測る。
        #   時間も一緒に伸ばすと、進むほど時間的な圧力が下がって本番から遠ざかる（実際にそうなっていた）。
        if b[2] / b[3] <= a[2] / a[3]:
            ng(f"第{b[0]}回: 1分あたりの分量が第{a[0]}回より増えていない"
               f"（{a[2]/a[3]:.0f}字/分→{b[2]/b[3]:.0f}字/分）＝進むほど楽になっている")
    # 注の手厚さも階段でなければならない。基礎で手厚く、本番で最小限にする。
    base = [r for r in ladder if r[1] == 1]; hon = [r for r in ladder if r[1] == 3]
    if base and hon and min(h[4] for h in hon) <= max(b[4] for b in base):
        ng("注の手厚さが階段になっていない（本番の回が基礎の回より注が細かい）："
           + str([(f"第{r[0]}回", f"{r[4]:.0f}字に1個") for r in ladder]))
    HONBAN_MAX = 20      # 共通テスト国語（90分5大問）で古文にあてる目安の上限
    for sid, lv, n, m, dens in ladder:
        if lv == 3 and m > HONBAN_MAX:
            ng(f"第{sid}回（本番）: 目安{m}分は本番の配分（{HONBAN_MAX}分）より緩い")

    # 8) 正解番号の分布
    if dist:
        mx, mn = max(dist.values()), min(dist.values())
        if mx - mn >= 4: ng(f"正解番号の偏り: {dict(sorted(dist.items()))}")

    if len(sys.argv) == 2:
        sys.exit("問題編と解答解説編の2つを渡すこと（1つだけでは照合できない）")
    if len(sys.argv) > 2:
        print("刷り上がりとの照合:")
        check_glyphs(sys.argv[1], "問題編"); check_glyphs(sys.argv[2], "解答解説編")
        check_layout(sys.argv[1], "問題編")   # 解答解説編は横組みで、縦線は表の罫なので対象外
        check_pdf(sets, sys.argv[1], sys.argv[2])

    print(f"\n題数 {len(sets)}／設問 {sum(len(S['questions']) for S in sets)}問／小問 {sum(len(q['items']) for S in sets for q in S['questions'])}個")
    print("レベルの階段:", [(f"第{a}回", LEVELS[b]['name'], f"{c}字", f"{d}分",
                              f"{c/d:.0f}字/分", f"注は{e:.0f}字に1個") for a, b, c, d, e in ladder])
    print("正解の分布:", dict(sorted(dist.items())))
    if refs: print("解説が指す注:", [f"第{a}回 注{b}＝{c}" for a, b, c in refs])
    if len(sys.argv) <= 2:
        print("※ 刷り上がりは検査していない（問題編と解答解説編のPDFを渡すと逆照合する）")
    print("問題なし" if not bad else f"要修正 {len(bad)} 件")
    sys.exit(1 if bad else 0)

if __name__ == "__main__":
    main()
