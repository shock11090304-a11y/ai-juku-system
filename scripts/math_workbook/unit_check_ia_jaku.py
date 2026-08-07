#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数学I·A 弱点発見トレーニングの【単元1つ】を検査する。執筆者が書き終えたら必ず回す。

  python3 unit_check_ia_jaku.py A07
  python3 unit_check_ia_jaku.py            # ★引数なし = 存在する全単元(刷るもの全部)

引数なしの既定を「見本1つ」にすると、実際に刷る単元が無検査のまま緑になる
(kaki_koushuu_eng で実際に起きた)。既定は必ず全部。
"""
import os, re, sys, inspect, traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _ia_jaku_lib as L

ALLOWED_TAGS = re.compile(r"</?(?:b|br)\s*/?>")
LEAK_ROOT = re.compile(r"(?m)^\s*(?:eq|ewline|abla|ot|u)\b")   # r-string 忘れの痕跡
REQUIRED = ("group", "level", "skill", "sub", "stem", "answer", "explanation", "chk")
SYMPY_HINTS = ("sp.", "sympy", "solve", "simplify", "expand", "factor", "Rational", "R(",
               "sqrt", "binomial", "Matrix", "for ", "range", "len(", "gcd", "divisors",
               "Poly", "nsimplify", "N(", "isprime", "sum(", "max(", "min(", "sorted",
               "statistics", "mean", "product", "permutations", "combinations", "Fraction")


def check_unit(code, do_katex=True):
    errs, warns = [], []
    try:
        mod = L.load_unit_module(code)
        unit = mod.UNIT
    except Exception as e:
        return [f"{code}: import 失敗 {type(e).__name__}: {e}\n{traceback.format_exc()}"], []

    # --- 単元が自分で用意した図の検査(ラベルと線の距離など)を実際に回す。
    #     ★ここが無いと、単元ファイルの中に検査を書いても誰も呼ばず、
    #       docstring だけが「見張っている」と主張する状態になる(A12 で実際に起きた)。
    for fn in getattr(mod, "FIG_CHECKS", []):
        try:
            for m in fn():
                errs.append(f"{code}: {m}")
        except Exception as e:
            errs.append(f"{code}: 図の検査 {getattr(fn, '__name__', fn)} が例外 "
                        f"{type(e).__name__}: {e}\n{traceback.format_exc()}")

    plan = L.PLAN_BY_CODE.get(code)
    if plan is None:
        errs.append(f"{code}: PLAN に無い単元コード")
        return errs, warns
    _, plan_name, plan_cnt, _area = plan

    if not unit.get("name"):
        errs.append(f"{code}: name が空")
    if not unit.get("tag"):
        warns.append(f"{code}: tag(目次の副題) が空")
    probs = unit.get("problems") or []
    if len(probs) != plan_cnt:
        errs.append(f"{code}: 問数が計画と違う ({len(probs)}問 / 計画 {plan_cnt}問)")

    # group が飛び飛びになっていないか(ビルダーは初出順に束ねるので見出しが重複する)
    seen, prev = [], None
    for q in probs:
        g = q.get("group", "")
        if g != prev:
            if g in seen:
                errs.append(f"{code}: group『{g}』が非連続(同じ見出しが2度出る)")
            seen.append(g)
            prev = g
    if len(seen) < 2:
        warns.append(f"{code}: group が {len(seen)} 個しかない(2〜4個が目安)")

    lv_count = {k: 0 for k in L.LEVELS}
    for j, q in enumerate(probs, 1):
        tag = f"{code}-{j}"
        for k in REQUIRED:
            if k not in q:
                errs.append(f"{tag}: キー '{k}' が無い")
        if errs and any(t.startswith(f"{tag}: キー") for t in errs):
            continue
        if q["level"] not in L.LEVELS:
            errs.append(f"{tag}: level が不正 {q['level']!r}")
        else:
            lv_count[q["level"]] += 1
        if q["skill"] not in L.SKILLS:
            errs.append(f"{tag}: skill コードが表に無い {q['skill']!r}")
        for s in q["sub"]:
            if s not in L.SKILLS:
                errs.append(f"{tag}: sub コードが表に無い {s!r}")
        # ★重み計算で二重計上され、un>=2 と MIN_WEAK_WRONG の両方の門を無効化する
        #   (1問誤答だけで weak=1.0 になる)。警告ではなくエラーにする。
        if q["skill"] in q["sub"]:
            errs.append(f"{tag}: sub に主スキルと同じコードが入っている(重みが二重計上される)")
        if len(set(q["sub"])) != len(q["sub"]):
            errs.append(f"{tag}: sub にコードの重複がある {q['sub']}")

        stem, ans, exp = q["stem"], q["answer"], q["explanation"]
        if not str(ans).strip():
            errs.append(f"{tag}: answer が空")
        # --- 解説の型
        if "▶" not in exp:
            errs.append(f"{tag}: 解説に ▶(なぜその方法か) が無い")
        if "①" not in exp:
            errs.append(f"{tag}: 解説に ①②③(手順) が無い")
        if "★" not in exp:
            errs.append(f"{tag}: 解説に ★(つまずき・合言葉) が無い")
        if len(exp.strip()) < 120:
            warns.append(f"{tag}: 解説が短い({len(exp.strip())}字)")
        if r"\dfrac" in exp:
            errs.append(f"{tag}: 解説に \\dfrac がある → \\frac にする"
                        f"(組分数の高さが行送りを超え、上下の行が物理的に重なる)")
        if LEAK_ROOT.search(exp):
            errs.append(f"{tag}: 解説が r-string でない可能性(\\n 始まりの LaTeX が改行に化けた痕跡)")
        # --- 数式の作法
        for field, text in (("stem", stem), ("answer", ans), ("explanation", exp)):
            if str(text).count("$") % 2:
                errs.append(f"{tag}: {field} の $ が奇数個(閉じ忘れ)")
            # ★1つの $...$ がソースの実改行をまたぐと、紙に生の LaTeX がそのまま印刷される。
            #   build_ia_jaku.detail() が実改行を <br> に変える → auto-render は隣接テキスト
            #   ノードしか連結しないので、<br>(要素ノード)をまたぐ開き $ と閉じ $ が対にならない。
            #   ズレは後続にも連鎖し、日本語が数式組版されることもある(A06-7 で実測)。
            #   $ の個数は偶数なので上のパリティ検査は通り、L.MATH_RE の [^$] は改行にも
            #   マッチするので下の katex_check も「1本の式」として通す＝既存ゲートの盲点。
            for seg in str(text).split("$")[1::2]:
                if "\n" in seg:
                    errs.append(f"{tag}: {field} の $...$ が実改行をまたいでいる → 行末で $ を閉じ、"
                                f"次行を新しい $ で開き直す(このままだと紙に生 LaTeX が印刷される)"
                                f"  ${' '.join(seg.split())[:60]}…$")
            for m in L.MATH_RE.finditer(str(text)):
                if L.CJK_RE.search(m.group(1)):
                    errs.append(f"{tag}: {field} の数式に日本語が入っている  ${m.group(1)[:40]}$")
            if re.search(r"\\,\s*\^\\circ", str(text)):
                errs.append(f"{tag}: {field} に \\,^\\circ がある(KaTeX が落ちる) → \\ ^\\circ か ^\\circ")
        # --- 生タグ
        for field, text in (("stem", stem), ("explanation", exp)):
            leftover = ALLOWED_TAGS.sub("", str(text))
            if "<" in leftover or ">" in leftover:
                errs.append(f"{tag}: {field} に <b>/<br> 以外の生タグらしき < > がある")
        # --- 図
        fig = q.get("figure")
        if fig:
            if "<svg" not in fig:
                errs.append(f"{tag}: figure が SVG でない")
            if "<script" in fig.lower() or re.search(r"\son[a-z]+\s*=", fig, re.I):
                errs.append(f"{tag}: figure に <script>/on* 属性(sanitizer で落ちる)")
            # ★紙に出るラベルの実寸。`size=(W,H)` は紙の大きさではないので、
            #   w_mm を渡し忘れると CSS の max-height:44mm がスケールを決め、
            #   viewBox の縦が大きい図ほどラベルが潰れる(実際に 6.40pt で出荷された)。
            info = L.fig_label_pts(fig)
            if info is None:
                errs.append(f"{tag}: figure に viewBox が無い(Canvas.svg() で作ること)")
            else:
                w_mm, h_mm, fixed, pts = info
                small = sorted(p for p in pts.values() if p < L.FIG_LABEL_MIN_PT)
                if small:
                    fs = min(k for k, v in pts.items() if v == small[0])
                    errs.append(
                        f"{tag}: 図のラベルが紙で {small[0]:.2f}pt しかない"
                        f"(font-size={fs:g} / 下限 {L.FIG_LABEL_MIN_PT}pt / 本文 9.7pt)。"
                        + ("w_mm を大きくする" if fixed else
                           f"svg(w_mm=…) を渡していないので CSS の "
                           f"max-height:{L.CSS_FIG_MAX_H_MM:g}mm がスケールを決めている"
                           f"(実効 {L.CSS_FIG_MAX_H_MM:g}mm ÷ viewBox の縦) → w_mm を渡す")
                        + f"  [紙 {w_mm:.1f}x{h_mm:.1f}mm]")
                if h_mm > 90 or w_mm > 145:
                    errs.append(f"{tag}: 図が紙で {w_mm:.1f}x{h_mm:.1f}mm と大きすぎる"
                                f"(本文の段幅は約152mm、ページの余白は約230mm)")
        # --- chk
        chk = q.get("chk")
        if not callable(chk):
            errs.append(f"{tag}: chk が callable でない")
        else:
            try:
                src = inspect.getsource(chk)
            except (OSError, TypeError):
                src = ""
            if src and not any(h in src for h in SYMPY_HINTS):
                warns.append(f"{tag}: chk が独立再計算に見えない(数値リテラルだけの恒真式かも) — 要確認")
            try:
                r = chk()
            except Exception as e:
                errs.append(f"{tag}: chk が例外 {type(e).__name__}: {e}")
            else:
                if r is not True:
                    errs.append(f"{tag}: chk が True を返さない → {r!r}")

    n = len(probs) or 1
    if lv_count["basic"] == 0:
        errs.append(f"{code}: [基礎] が 0 問(各単元の先頭に基礎を置く)")
    if lv_count["basic"] / n > 0.7:
        warns.append(f"{code}: [基礎] が {lv_count['basic']}/{n} と多すぎる")
    if lv_count["advanced"] > n * 0.4:
        warns.append(f"{code}: [発展] が {lv_count['advanced']}/{n} と多すぎる")

    # --- KaTeX に実際に通す(生ソース印刷を防ぐ最重要ゲート)
    if do_katex and not errs:
        pairs = L.unit_math(unit)
        bad = L.katex_check([e for e, _ in pairs], tmp_tag=code)
        where = {}
        for e, w in pairs:
            where.setdefault(e, []).append(w)
        for e, msg in bad:
            errs.append(f"{code}: KaTeX 失敗  ${e}$  → {msg}  (出現: {', '.join(where.get(e, [])[:4])})")
    return errs, warns


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    no_katex = "--no-katex" in sys.argv
    if args:
        codes = [a.upper() for a in args]
    else:
        codes = sorted(f[:-3] for f in os.listdir(L.PARTS_DIR)
                       if re.fullmatch(r"A\d\d\.py", f))
    if not codes:
        sys.exit("検査対象の単元ファイルが1つも無い (parts_ia_jaku/A01.py …)")
    # ★KaTeX の実レンダリングは Chrome を起動する。CI(ubuntu)には無いので、
    #   そこで落ちると material-gates ジョブごと赤になる(この教材以外も道連れ)。
    #   ★外したことは必ず印字する。黙って減らすと「全部通った」に見える。
    if not no_katex and not os.path.exists(L.CHROME):
        no_katex = True
        print(f"SKIP KaTeX 実レンダリング: Chrome が無い ({L.CHROME})\n"
              f"     → 紙に生 LaTeX が出ないかは**手元で** python3 unit_check_ia_jaku.py を回して見ること")
    print(f"検査対象: {', '.join(codes)}  (計 {len(codes)} 単元)")
    tot_e = tot_w = 0
    for c in codes:
        e, w = check_unit(c, do_katex=not no_katex)
        tot_e += len(e); tot_w += len(w)
        print(f"\n--- {c} ---  ERROR {len(e)} / WARN {len(w)}")
        for m in e:
            print("  ✗", m)
        for m in w:
            print("  ! ", m)
    print(f"\n===== ERROR {tot_e} / WARN {tot_w} =====")
    if tot_e:
        print("NG — 直してから報告すること")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
