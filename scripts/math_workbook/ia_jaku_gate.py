#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数学I·A 弱点発見トレーニングの【総点検ゲート】。刷る前に必ず回す。

  python3 ia_jaku_gate.py              # 全部(PDFの検査も含む)
  python3 ia_jaku_gate.py --no-pdf     # データだけ(CI 用・PDF はリポジトリに無い)

検査するもの:
  1. 単元ごとの検査(unit_check_ia_jaku)を全単元
  2. 全 $...$ を実際に KaTeX へ通す        … 落ちた数式は紙に生ソースで印刷される
  3. 診断マップと問題集のドリフト           … 印刷版とデータ版のズレ
  4. カバレッジ(担当0問のスキル)             … 弱点特化で分野を絞ると外側が丸ごと落ちる
  5. 解答漏洩(group見出し・目次・単元内)
  6. 既存問題集との実質重複
  7. 出来た全 PDF に生の LaTeX が残っていないか  … ★作った PDF は全部見る
  8. 出来た全 PDF の字形の物理的な重なり         … 行送り不足で分母が指数に乗る
  9. 出来た全 PDF の空白ページ

★ exit 1 を返さないゲートは「検査していない」のと同じ。違反があれば必ず落とす。
"""
import os, re, sys, subprocess, collections
import fitz

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _ia_jaku_lib as L
import build_kiso as K

OUTPUTS = ["数学IA_弱点発見トレーニング.pdf",
           "数学IA_弱点発見トレーニング_自己採点シート.pdf",
           "数学IA_弱点発見トレーニング_診断キー_塾長用.pdf"]

# 生の LaTeX が紙に出ていないかを見るための痕跡
RAW_TEX = re.compile(r"\\(?:mathrm|dfrac|frac|sqrt|times|leqq|geqq|circ|sin|cos|tan|angle|"
                     r"triangle|overline|left|right|sum|cdot|neq|pm)\b|\$")
# 「答えを言ってしまっている見出し」の痕跡
LEAK_WORDS = ["である", "になる", "は正", "は負", "でない", "とは限らない", "成り立つ", "成り立たない",
              "個", "通り", "真である", "偽である"]

XPAD, YPAD, LINE_GAP = 0.4, 0.8, 8.0


def h(title):
    print(f"\n===== {title} =====")


# ------------------------------------------------------------------ 1. 単元検査
def gate_units():
    codes = sorted(f[:-3] for f in os.listdir(L.PARTS_DIR) if re.fullmatch(r"A\d\d\.py", f))
    plan = [c for c, *_ in L.PLAN]
    h(f"1. 単元検査 ({len(codes)}単元: {', '.join(codes)})")
    missing = [c for c in plan if c not in codes]
    extra = [c for c in codes if c not in plan]
    bad = 0
    if missing:
        print(f"  NG 単元ファイルが無い: {missing}")
        bad += len(missing)
    if extra:
        print(f"  NG PLAN に無い単元ファイル: {extra}")
        bad += len(extra)
    r = subprocess.run([sys.executable, os.path.join(HERE, "unit_check_ia_jaku.py")],
                       capture_output=True, text=True, cwd=HERE)
    tail = [ln for ln in r.stdout.splitlines() if ln.startswith("  ✗")]
    print(r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "(出力なし)")
    for ln in tail[:20]:
        print(ln)
    return bad + (0 if r.returncode == 0 else max(1, len(tail)))


# ------------------------------------------------------------------ 2. KaTeX
def gate_katex():
    import content_ia_jaku as C
    for p in C.PARTS:
        K.reorder(p["units"])
    found = collections.defaultdict(list)
    for code, u in zip(C.CODES, C.UNITS):
        for j, q in enumerate(u["problems"], 1):
            for field in ("stem", "answer", "explanation"):
                for m in L.MATH_RE.finditer(q.get(field) or ""):
                    found[m.group(1)].append(f"{code}-{j}:{field}")
    for area, txt in C.PART_POINTS.items():
        for m in L.MATH_RE.finditer(txt):
            found[m.group(1)].append(f"攻略ボックス:{area}")
    h(f"2. KaTeX 実レンダリング ({len(found)} 式)")
    bad = L.katex_check(list(found), tmp_tag="gate")
    for e, msg in bad:
        print(f"  NG ${e}$ → {msg}  (出現: {', '.join(found[e][:4])})")
    if not bad:
        print(f"  OK 全 {len(found)} 式がパースできる")
    return len(bad)


# ------------------------------------------------------------------ 3. ドリフト
def gate_drift():
    h("3. 診断マップと問題集のドリフト")
    if not os.path.exists(os.path.join(HERE, "diagnosis_ia_jaku.py")):
        print("  NG diagnosis_ia_jaku.py が無い → python3 gen_diagnosis_ia_jaku.py")
        return 1
    r = subprocess.run([sys.executable, os.path.join(HERE, "analyze_ia_jaku.py"), "A01-1"],
                       capture_output=True, text=True, cwd=HERE)
    if r.returncode != 0:
        print("  NG " + (r.stderr or r.stdout).strip().splitlines()[-1])
        return 1
    print("  OK 印刷版とデータ版が一致")
    return 0


# ------------------------------------------------------------------ 4. カバレッジ
def gate_coverage():
    import diagnosis_ia_jaku as D
    h("4. スキルのカバレッジ")
    used = {m["skill"] for m in D.MAP.values()} | {c for m in D.MAP.values() for c in m["sub"]}
    unused = [c for c in L.SKILLS if c not in used]
    prim = collections.Counter(m["skill"] for m in D.MAP.values())
    thin = [c for c in L.SKILLS if c in used and prim[c] == 0]
    # ★担当(主+副)が1問しかないスキルは、analyze の MIN_WEAK_WRONG=2 により
    #   **構造的に弱点と断定できない**(永久に「要再測」で、再測に使う2問目も無い)。
    #   担当0問だけを見ていると、この穴は緑のまま通る。
    carry = collections.Counter()
    for m in D.MAP.values():
        carry[m["skill"]] += 1
        for c in m["sub"]:
            carry[c] += 1
    lone = [c for c in L.SKILLS if carry[c] == 1]
    if unused:
        print(f"  NG 1問も担当が無いスキル {len(unused)}件: "
              + "、".join(f"{c}({L.SKILLS[c]})" for c in unused))
    if lone:
        print(f"  NG 担当が1問しかないスキル {len(lone)}件(弱点断定できない): "
              + "、".join(f"{c}({L.SKILLS[c]})" for c in lone))
    if thin:
        print(f"  ! 副スキルとしてしか出ないスキル {len(thin)}件: "
              + "、".join(f"{c}({L.SKILLS[c]})" for c in thin))
    if not unused and not lone:
        print(f"  OK 全 {len(L.SKILLS)} スキルに担当問題が2問以上ある")
    return len(unused) + len(lone)


# ------------------------------------------------------------------ 5. 漏洩
def norm(s):
    """比較用の正規化(空白・記号・LaTeX の飾りを落とす)。"""
    s = re.sub(r"\\[a-zA-Z]+|[{}$\\\s,.、。（）()\[\]　]", "", s)
    return s


def gate_leak():
    import content_ia_jaku as C
    for p in C.PARTS:
        K.reorder(p["units"])
    h("5. 解答漏洩")
    bad = 0
    for code, u in zip(C.CODES, C.UNITS):
        for j, q in enumerate(u["problems"], 1):
            g = q.get("group", "")
            a = norm(q.get("answer", ""))
            # (a) 見出しが答えそのものを言っている
            if a and len(a) >= 3 and a in norm(g):
                print(f"  NG {code}-{j}: group『{g}』が答え『{q['answer']}』を含む(見出しは問題編にも印刷される)")
                bad += 1
            # (b) 見出しが結論の語を使っている(判定を問う設問だけ対象)
            if any(w in g for w in LEAK_WORDS) and ("か" in q["stem"] or "判定" in q["stem"]
                                                    or "調べ" in q["stem"]):
                print(f"  ! {code}-{j}: group『{g}』が結論の語を含む × 判断を問う設問 — 要目視")
            # (c) 同じ単元の後の問題文が、前の問題の答えを与件にしている
            for k, q2 in enumerate(u["problems"][j:], j + 1):
                if a and len(a) >= 5 and a in norm(q2["stem"]):
                    print(f"  NG {code}-{j} の答えが {code}-{k} の問題文に出ている")
                    bad += 1
    # (d) 目次の tag が答えを言っていないか(印刷される)
    for code, u in zip(C.CODES, C.UNITS):
        for j, q in enumerate(u["problems"], 1):
            a = norm(q.get("answer", ""))
            if a and len(a) >= 4 and a in norm(u.get("tag", "")):
                print(f"  NG 目次の副題『{u['tag']}』が {code}-{j} の答えを含む")
                bad += 1
    if not bad:
        print("  OK 機械検出できる漏洩なし")
    return bad


# ------------------------------------------------------------------ 6. 重複
def gate_dup():
    h("6. 既存問題集との実質重複")
    r = subprocess.run([sys.executable, os.path.join(HERE, "dup_check_ia_jaku.py")],
                       capture_output=True, text=True, cwd=HERE)
    print(r.stdout.strip() or "(出力なし)")
    return 0 if r.returncode == 0 else 1


# ------------------------------------------------------------------ 7-9. 紙
def gate_pdfs():
    h("7-9. 出来た PDF の検査(生LaTeX / 文字の重なり / 空白ページ)")
    bad = 0
    for name in OUTPUTS:
        path = os.path.join(HERE, name)
        if not os.path.exists(path):
            # ★未生成を「(未生成)」で素通りさせない。検査していないのに緑になる。
            print(f"  NG {name}: PDF が無い＝この紙は検査できていない(build を回すこと)")
            bad += 1
            continue
        doc = fitz.open(path)
        raw = [i for i, pg in enumerate(doc, 1) if RAW_TEX.search(pg.get_text())]
        blank = [i for i, pg in enumerate(doc, 1)
                 if i > 1 and len(pg.get_text().strip()) < 3 and not pg.get_images()]
        ov = 0
        ov_ex = []
        for i, pg in enumerate(doc, 1):
            hits = overlaps(pg)
            if hits:
                ov += len(hits)
                if len(ov_ex) < 3:
                    ov_ex.append(f"p{i} '{hits[0][0]}'×'{hits[0][1]}'")
        if raw:
            print(f"  NG {name}: 生の LaTeX が {len(raw)}ページに残っている (例 p{raw[0]})")
            bad += len(raw)
        if ov:
            print(f"  NG {name}: 字形の物理的な重なり {ov}件  例 {', '.join(ov_ex)}")
            bad += ov
        if blank:
            print(f"  ! {name}: 空白ページ {len(blank)}枚 (p{', p'.join(map(str, blank[:6]))})")
        if not raw and not ov:
            print(f"  OK {name}: {doc.page_count}ページ・生LaTeXなし・重なりなし"
                  + (f"・空白{len(blank)}枚" if blank else ""))
        doc.close()
    return bad


def overlaps(page):
    """行またぎの字形の物理的な重なり。LINE_GAP 未満は同じ行(添字と本体)なので対象外。"""
    cs = []
    for blk in page.get_text("rawdict")["blocks"]:
        for line in blk.get("lines", []):
            for span in line["spans"]:
                for ch in span["chars"]:
                    if ch["c"].strip():
                        cs.append((fitz.Rect(ch["bbox"]), ch["c"]))
    buckets = collections.defaultdict(list)
    for r, c in cs:
        for b in range(int(r.x0 // 20), int(r.x1 // 20) + 1):
            buckets[b].append((r, c))
    hits, seen = [], set()
    for items in buckets.values():
        for i in range(len(items)):
            r1, c1 = items[i]
            for j in range(i + 1, len(items)):
                r2, c2 = items[j]
                if abs((r1.y0 + r1.y1) / 2 - (r2.y0 + r2.y1) / 2) < LINE_GAP:
                    continue
                ox = min(r1.x1, r2.x1) - max(r1.x0, r2.x0)
                oy = min(r1.y1, r2.y1) - max(r1.y0, r2.y0)
                if ox > XPAD and oy > YPAD:
                    key = (round(r1.x0, 1), round(r1.y0, 1), round(r2.x0, 1), round(r2.y0, 1))
                    if key not in seen:
                        seen.add(key)
                        hits.append((c1, c2))
    return hits


# KaTeX の scriptscript(分数の中の指数)は原理的に 0.41em まで落ちるので、これ以上は
# 本文サイズを上げるしか手が無い。基準は**塾長が受け取り済みの第2集の実測**に合わせる:
#   第2集: 最小 4.39pt / 5.0pt 未満が 39 個
#   本書 : 最小 4.73pt / 5.0pt 未満が  5 個  ← 既に上回っている
# 4.6pt(=1.6mm) を割ったら退行とみなして落とす。5.5pt 未満の個数は警告として出す。
MIN_PT = 4.6
WARN_PT = 5.5
# ★KaTeX は vlist の高さ合わせに 0.7pt のゼロ幅スペース(U+200B)を大量に置く。
#   これを数えると 1253 個の「極小文字」が出て本物の 5 個が埋もれる。見えない文字は除く。
INVISIBLE = "\u200b\u200c\u200d\ufeff\u00ad"


BAD_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\ufffd\uf000-\uf8ff]")


# @page margin: 20mm 18mm 17mm 18mm / A4 841.92pt → 本文の下端は 841.92 - 17mm(48.2pt) = 793.7pt。
# ノンブル(fitz が h-22 に刻印)と柱(y=34)は本文ではないので除外する。
# 冊子ごとに @page の下マージンが違う(A4=841.92pt)。ここを1つの定数にすると
# シート・診断キーで偽陽性が出る。
MM = 72 / 25.4
BODY_BOTTOM = {
    OUTPUTS[0]: 841.92 - 17 * MM,   # 問題集 @page margin-bottom:17mm
    OUTPUTS[1]: 841.92 - 8 * MM,    # 自己採点シート 8mm
    OUTPUTS[2]: 841.92 - 13 * MM,   # 診断キー 13mm
}
NOMBRE_TOP = 806.0                  # fitz がノンブルを刻印する帯(本文ではない)
# 版面の下端で Chrome がクリップするので、はみ出しは「上端の切れ端」として紙に出る。
# 切れ端の高さがこれ以上なら文字として読めてしまう＝刷り直し。それ未満は塵として警告に留める。
# (実測: KaTeX の行箱は vlist の height:0 のせいで残り 2pt でも1行入ると判定され、
#  2.1pt の切れ端が出る。中身は次ページに完全に出るので欠落はしない。)
VISIBLE_NG = 4.0


def gate_overflow():
    """本文が版面(下マージン)にはみ出していないか。

    ★`break-inside: avoid` を付けた 1問ブロックが残りスペースに入りきらないとき、
      Chrome は改ページせずに**下マージンへあふれさせる**ことがある。紙では
      版面の外に文字の切れ端が出る(実測7ページ・ノンブルまで 7pt)。
      PDF は正常に生成され、文字抽出でも普通に読めるので実物を見るまで気づけない。
    """
    h("12. 版面からのはみ出し(下マージン)")
    bad = 0
    for name in OUTPUTS:
        path = os.path.join(HERE, name)
        if not os.path.exists(path):
            continue
        hits = []
        bottom = BODY_BOTTOM[name]
        for i, pg in enumerate(fitz.open(path), 1):
            for blk in pg.get_text("dict")["blocks"]:
                for ln in blk.get("lines", []):
                    for sp in ln.get("spans", []):
                        t = sp.get("text", "").replace("\u200b", "")
                        if not t.strip():
                            continue
                        y0, y1 = sp["bbox"][1], sp["bbox"][3]
                        if bottom < y1 < max(NOMBRE_TOP, bottom + 12):
                            hits.append((i, round(bottom - y0, 2), t[:12]))
        big = [x for x in hits if x[1] >= VISIBLE_NG]
        if big:
            pages = sorted({p for p, _, _ in big})
            print(f"  NG {name}: 版面外に読める大きさの切れ端 {len(big)}箇所 / {len(pages)}ページ "
                  f"(例 p{big[0][0]} 露出 {big[0][1]}pt {big[0][2]!r})")
            bad += len(pages)
        elif hits:
            pages = sorted({p for p, _, _ in hits})
            print(f"  ! {name}: 下マージンに塵 {len(hits)}箇所 / {len(pages)}ページ "
                  f"(最大 {max(x[1] for x in hits)}pt・中身は次ページに完全に出る)")
        else:
            print(f"  OK {name}: 版面からのはみ出しなし")
    return bad


def gate_tofu():
    """紙に制御文字・豆腐(□)・私用領域が出ていないか。

    ★実際に踏んだ事故: fitz の stamp_pdf は最後に subset_fonts() でフォントを
      使用グリフだけに削る。その**後**に insert_text で別の文字を差すと、字が
      埋め込まれておらず柱が丸ごと \x00\x00\x00 になった。PDF は正常に生成され、
      ページ数も変わらないので実物を拡大するまで気づけない。
    """
    h("11. 制御文字・豆腐")
    bad = 0
    for name in OUTPUTS:
        path = os.path.join(HERE, name)
        if not os.path.exists(path):
            continue
        hits = []
        for i, pg in enumerate(fitz.open(path), 1):
            m = BAD_CHARS.search(pg.get_text())
            if m:
                hits.append((i, repr(m.group(0))))
        if hits:
            print(f"  NG {name}: {len(hits)}ページに制御文字/豆腐  例 p{hits[0][0]} {hits[0][1]}")
            bad += len(hits)
        else:
            print(f"  OK {name}: 制御文字・豆腐なし")
    return bad


def gate_glyph_size():
    """紙に出た文字が小さすぎないか。★インラインの \\frac は分子分母が 0.7em に落ち、
    指数の中に入ると 0.49em になる。PDF は正常に出るので実物を拡大するまで気づけない。"""
    h("10. 最小グリフサイズ(紙で読めるか)")
    bad = 0
    for name in OUTPUTS:
        path = os.path.join(HERE, name)
        if not os.path.exists(path):
            continue
        worst, worst_p, cnt, warn = 99.0, 0, 0, 0
        for i, pg in enumerate(fitz.open(path), 1):
            for blk in pg.get_text("dict")["blocks"]:
                for line in blk.get("lines", []):
                    for span in line.get("spans", []):
                        t = span.get("text", "")
                        for ch in INVISIBLE:
                            t = t.replace(ch, "")
                        if not t.strip():
                            continue
                        sz = span["size"]
                        if sz < WARN_PT:
                            warn += 1
                        if sz < MIN_PT:
                            cnt += 1
                        if sz < worst:
                            worst, worst_p = sz, i
        if cnt:
            print(f"  NG {name}: {MIN_PT}pt 未満の文字が {cnt} 個 "
                  f"(最小 {worst:.2f}pt / p{worst_p}) — 紙で判読できない")
            bad += 1
        elif worst > 90:
            print(f"  NG {name}: 文字が1つも無い(空のPDF)")
            bad += 1
        else:
            print(f"  OK {name}: 最小 {worst:.2f}pt"
                  + (f"（{WARN_PT}pt 未満が {warn} 個 — 分数の中の指数。第2集は39個）" if warn else ""))
    return bad


def main():
    no_pdf = "--no-pdf" in sys.argv
    bad = 0
    bad += gate_units()
    bad += gate_katex()
    bad += gate_drift()
    bad += gate_coverage()
    bad += gate_leak()
    bad += gate_dup()
    if no_pdf:
        print("\n===== 7-9. PDF の検査 =====\n  SKIP (--no-pdf) "
              "★紙の検査は手元で build 後に --no-pdf 無しで回すこと")
    else:
        bad += gate_pdfs()
        bad += gate_glyph_size()
        bad += gate_tofu()
        bad += gate_overflow()
    print(f"\n{'=' * 60}\n違反 {bad} 件")
    if bad:
        print("NG — 直すまで刷らない")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
