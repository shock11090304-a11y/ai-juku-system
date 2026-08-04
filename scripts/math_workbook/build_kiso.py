#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数列・確率・ベクトル 基礎徹底問題集 を KaTeX 教科書組版で PDF 化する。

  python3 build_kiso.py

content_kiso.PARTS(確率/数列/ベクトルの3編)を「部扉つき」で問題編/解答編に組む。
数式描画の部品(prob_html / ans_html / stamp_pdf / KATEX)は build_html から再利用し、
このスクリプトは 3編の部扉・目次の編見出し・表紙まわりだけを担当する。
"""
import os, sys, subprocess, datetime, html as _html
import fitz
import importlib
import build_html as B          # 描画部品を再利用(prob_html, ans_html, stamp_pdf, esc, KATEX)

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- 巻の定義
# ★以前は content_kiso 専用に固定されていた。巻を増やすたびにビルダーを複製すると
#   組版の修正が片方にしか効かないので、ここに1行足すだけで新しい巻を出せるようにする。
#     python3 build_kiso.py          # 既定(数列確率ベクトル)
#     python3 build_kiso.py suuA     # 数A(図形の性質・整数)
VOLUMES = {
    "kiso": {
        "content": "content_kiso", "expl": "explanations_kiso",
        "out": "数列確率ベクトル_基礎徹底問題集.pdf",
        "title": "数列・確率・ベクトル", "subtitle": "基礎徹底 問題演習ドリル",
        "tagline": "高校3年 ／ 苦手分野を「基礎の基礎」からやり直す",
        "book": "数列・確率・ベクトル 基礎徹底問題集",
        "howto": ("【この問題集の使い方】確率・数列・ベクトルを、いちばんやさしい問題から順に並べました。"
                  "各問には〔基礎〕〔標準〕〔発展〕の目安をつけています。解説は、途中の式を省かずに"
                  "「▶なぜその方法を使うのか → ①②③手順 → ★つまずきやすい所と合言葉」の順で書いています。"
                  "分からなかった問題は、解説をそのままノートに写してから、何も見ずにもう一度解くのが"
                  "最強の勉強法です。"
                  "各単元の解答の最初にある「この単元のキモ」を先に読んでから解き始めてもかまいません。"),
    },
    "suuA": {
        "content": "content_kisoA", "expl": "explanations_kisoA",   # POINTS(単元のキモ)のみ
        "out": "数学A_図形と整数_基礎徹底問題集.pdf",
        "title": "数学A　図形の性質・整数の性質", "subtitle": "基礎徹底 問題演習ドリル",
        "tagline": "高校1〜3年 ／ 図形の性質と整数分野を「基礎の基礎」からやり直す",
        "book": "数学A 図形の性質・整数の性質 基礎徹底問題集",
        "howto": ("【この問題集の使い方】図形の性質と整数の性質を、いちばんやさしい問題から順に並べました。"
                  "各問には〔基礎〕〔標準〕〔発展〕の目安をつけています。"
                  "図形は必ず自分で図をかいてから解くこと。整数は「余りで分類する」「積の形にする」の"
                  "2つが軸になります。"
                  "分からなかった問題は、解説をそのままノートに写してから、何も見ずにもう一度解くのが"
                  "最強の勉強法です。"),
    },
    "suuI": {
        "content": "content_kisoI", "expl": "explanations_kisoI",
        "out": "数学I_基礎徹底問題集.pdf",
        "title": "数学I　数と式・二次関数・図形と計量", "subtitle": "基礎徹底 問題演習ドリル",
        "tagline": "高校1〜3年 ／ すべての土台を「基礎の基礎」からやり直す",
        "book": "数学I 基礎徹底問題集",
        "howto": ("【この問題集の使い方】数学Iは、数II以降のすべてが乗る土台です。"
                  "各問には〔基礎〕〔標準〕〔発展〕の目安をつけています。"
                  "二次関数は必ず平方完成から、二次不等式は必ずグラフをかいてから解くこと。"
                  "分からなかった問題は、解説をそのままノートに写してから、何も見ずに"
                  "もう一度解くのが最強の勉強法です。"),
    },
    "suuII": {
        "content": "content_kisoII", "expl": "explanations_kisoII",
        "out": "数学II_基礎徹底問題集.pdf",
        "title": "数学II　三角関数・指数対数・微分積分", "subtitle": "基礎徹底 問題演習ドリル",
        "tagline": "高校2〜3年 ／ 脱落が集中する4分野を基礎からやり直す",
        "book": "数学II 基礎徹底問題集",
        "howto": ("【この問題集の使い方】高2以降でつまずきが集中する4分野を集めました。"
                  "三角関数は弧度法と単位円、対数は「$a$ を何乗すると $M$ か」という定義に"
                  "毎回もどるのがコツです。"
                  "対数の方程式・不等式では【真数条件】の確認を必ず最後に行うこと。"
                  "分からなかった問題は、解説をそのままノートに写してから、何も見ずに"
                  "もう一度解くのが最強の勉強法です。"),
    },
    "suuIII": {
        "content": "content_kisoIII", "expl": "explanations_kisoIII",
        "out": "複素数平面_確率分布_数III_基礎徹底問題集.pdf",
        "title": "複素数平面・確率分布・数学III", "subtitle": "基礎徹底 問題演習ドリル",
        "tagline": "高校2〜3年 ／ 数C・数B・数III を基礎からやり直す",
        "book": "複素数平面・確率分布・数学III 基礎徹底問題集",
        "howto": ("【この問題集の使い方】共通テストの選択問題（複素数平面・統計的な推測）と、"
                  "理系2次で必須の数学III（極限・微分法・積分法）をまとめました。"
                  "複素数は「平面上の点」と見ること、確率分布は $E$ と $V$ の性質の違い、"
                  "数IIIは「微分は公式3つ、積分は置換と部分積分の2本柱」が軸です。"
                  "★数III（第3〜5編）は共通テストには出ません。志望校の出題範囲を"
                  "確認してから取り組んでください。"),
    },
}
VOL = VOLUMES[sys.argv[1]] if len(sys.argv) > 1 and sys.argv[1] in VOLUMES else VOLUMES["kiso"]

C = importlib.import_module(VOL["content"])
E = importlib.import_module(VOL["expl"]) if VOL["expl"] else None
OUT = os.path.join(HERE, VOL["out"])
TITLE, SUBTITLE = VOL["title"], VOL["subtitle"]
TAGLINE, BOOK, HOWTO = VOL["tagline"], VOL["book"], VOL["howto"]


def reorder(units):
    """build_html と同じ規則: 同 group を初出順に連続化し no を採番。"""
    for u in units:
        order, buckets = [], {}
        for q in u["problems"]:
            g = q.get("group", "")
            if g not in buckets:
                buckets[g] = []
                order.append(g)
            buckets[g].append(q)
        u["problems"] = [q for g in order for q in buckets[g]]
        for j, q in enumerate(u["problems"], 1):
            q["no"] = j
    return units


def toc_html(parts):
    rows = []
    ui = 1
    for p in parts:
        rows.append(f'<div class="toc-part">{B.esc(p["area"])}</div>')
        for u in p["units"]:
            rows.append(
                f'<div class="toc-row"><span class="toc-no">{ui:02d}</span>'
                f'<span class="toc-name">{B.esc(u["name"])}</span>'
                f'<span class="toc-tag">{B.esc(u.get("tag",""))}</span>'
                f'<span class="toc-n">{len(u["problems"])}問</span></div>')
            ui += 1
    return "".join(rows)


def detail_html(s):
    """詳細解説テキスト → HTML。実改行を <br> に(esc は &<> のみで $ や \\ は不変)。"""
    return B.esc(s).replace("\n", "<br>")


def ans_html_detailed(q, ui):
    """解答行 + 詳細解説(explanations_kiso のオーバーレイ)。無ければ従来の短い解説。
    答え行(.ansline)は直後の解説と切り離さない(赤字だけページ末尾に孤立するのを防ぐ)。"""
    a = B.esc(q.get("answer", ""))
    exp = E.EXPL.get(f"{ui}-{q['no']}") if E is not None else None
    body = detail_html(exp) if exp else B.esc(q.get("explanation", ""))
    return (f'<div class="prob"><div class="ansline"><span class="no">{q["no"]}.</span> '
            f'<span class="ans">{a}</span></div>'
            f'<div class="exp">{body}</div></div>')


def section_html(parts, kind):
    """kind: 'prob' or 'ans'。編ごとに部扉を挟み、各単元を band + group で組む。"""
    out = []
    ui = 1
    kicker = "問題" if kind == "prob" else "解答"
    for p in parts:
        out.append(f'<div class="pdiv"><h2>{B.esc(p["area"])}</h2>'
                   f'<div class="d-sub">{B.esc(p.get("sub",""))}</div></div>')
        for u in p["units"]:
            out.append('<section class="unit">')
            out.append(f'<div class="band"><div class="band-k">{kicker}　{ui:02d}</div>'
                       f'<div class="band-t">{B.esc(u["name"])}</div></div>')
            if kind == "ans" and E is not None and ui in E.POINTS:
                out.append(f'<div class="pointbox"><div class="pb-t">◆ この単元のキモ（先に読む）</div>'
                           f'{detail_html(E.POINTS[ui])}</div>')
            cur = None
            for q in u["problems"]:
                g = q.get("group", "")
                if g != cur:
                    cur = g
                    out.append(f'<h3 class="grp">■ {B.esc(g)}</h3>')
                out.append(B.prob_html(q) if kind == "prob" else ans_html_detailed(q, ui))
            out.append('</section>')
            ui += 1
    return "\n".join(out)


CSS = """
@page { size: A4; margin: 20mm 18mm 17mm 18mm; }
* { box-sizing: border-box; }
body { font-family: "Hiragino Mincho ProN","Yu Mincho",serif; color:#1a1a1a; font-size:10.5pt; line-height:1.65; margin:0; }
.sans { font-family:"Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif; }
.katex { font-size:1.02em; }
/* 表紙 */
.cover { height: 247mm; position: relative; page-break-after: always; }
.cover .cband { position:absolute; top:-20mm; left:-18mm; width:210mm; height:70mm; background:#1f3a5f; }
.cover .rule { position:absolute; top:50mm; left:-18mm; width:210mm; height:2mm; background:#c8a24e; }
.cover .title { position:absolute; top:88mm; width:100%; text-align:center; font-family:"Hiragino Kaku Gothic ProN",sans-serif; }
.cover .title h1 { color:#1f3a5f; font-size:30pt; margin:0; letter-spacing:2px; }
.cover .title .sub { color:#1f3a5f; font-size:15pt; margin-top:6px; }
.cover .title .tag { color:#444; font-size:12.5pt; margin-top:18px; font-weight:normal; }
.cover .title .meta { color:#444; font-size:11.5pt; margin-top:6px; }
.cover .foot { position:absolute; top:180mm; width:100%; text-align:center; color:#8a8a8a; font-size:10.5pt; font-family:sans-serif; }
/* 大扉(問題編/解答編) */
.divider { height:247mm; page-break-before:always; page-break-after:always; display:flex; flex-direction:column; justify-content:center; align-items:center; }
.divider h2 { color:#1f3a5f; font-size:22pt; font-family:"Hiragino Kaku Gothic ProN",sans-serif; margin:0; }
.divider .d-sub { color:#444; font-size:12pt; margin-top:8px; }
/* 編の部扉 */
.pdiv { page-break-before:always; padding-top:78mm; text-align:center; }
.pdiv h2 { color:#1f3a5f; font-size:26pt; font-family:"Hiragino Kaku Gothic ProN",sans-serif; margin:0; letter-spacing:3px; }
.pdiv .d-sub { color:#555; font-size:12pt; margin-top:12px; }
/* 目次 */
.toc { page-break-after: always; }
.toc h2 { color:#1f3a5f; text-align:center; font-size:20pt; font-family:"Hiragino Kaku Gothic ProN",sans-serif; }
.toc-part { color:#1f3a5f; font-weight:bold; font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-size:11.5pt; margin:12px 0 3px; border-bottom:1.6px solid #1f3a5f; padding-bottom:3px; }
.toc-row { display:flex; align-items:center; border-bottom:0.5px solid #c9d4e0; padding:5px 2px; }
.toc-no { color:#1f3a5f; font-weight:bold; width:34px; font-family:sans-serif; }
.toc-name { flex:0 0 38%; font-family:"Hiragino Kaku Gothic ProN",sans-serif; }
.toc-tag { flex:1; color:#8a8a8a; font-size:9.5pt; }
.toc-n { color:#8a8a8a; font-size:9.5pt; }
.howto { margin-top:14px; color:#444; font-size:10pt; background:#f4f6f9; border-left:3px solid #c8a24e; padding:10px 12px; line-height:1.75; }
/* 単元 */
.unit { page-break-before: always; }
.band { background:#1f3a5f; color:#fff; padding:8px 12px 10px; margin-bottom:8px; }
.band-k { font-size:10pt; font-family:sans-serif; opacity:.9; }
.band-t { font-size:16pt; font-family:"Hiragino Kaku Gothic ProN",sans-serif; margin-top:1px; }
.grp { color:#1f3a5f; font-size:11pt; font-family:"Hiragino Kaku Gothic ProN",sans-serif; margin:10px 0 4px; break-after: avoid; page-break-after: avoid; }
.prob { margin:3px 0 6px; padding-left:19px; text-indent:-19px; break-inside: avoid; page-break-inside: avoid; }
/* ★図(SVG)のサイズ制約。build_html.py 側の CSS にはあるが、build_kiso.py は
   独自の CSS を持つため、ここに書かないと図がページ全面に引き伸ばされる（実際にそうなった）。 */
.fig { text-indent:0; text-align:center; margin:4px 0 2px; }
.fig svg { max-width:62mm; max-height:44mm; height:auto; }
.fig svg text { font-family:"Hiragino Kaku Gothic ProN",sans-serif; }
.prob .no { color:#1f3a5f; font-weight:bold; }
.lv { font-size:8pt; }
.ans { color:#c8492e; font-weight:bold; }
.exp { text-indent:0; padding-left:2px; color:#333; font-size:9.5pt; margin-top:3px; line-height:1.8; }
.ansline { break-after: avoid; page-break-after: avoid; }
/* 解答編: 詳細解説つきの問題は長いので、途中改ページを許す(1問丸ごと避けると空白が出る) */
.prob:has(.exp br) { break-inside: auto; page-break-inside: auto; }
.pointbox { background:#f4f6f9; border:1.2px solid #1f3a5f; border-radius:4px;
            padding:9px 12px; margin:4px 0 10px; font-size:9.5pt; line-height:1.85; color:#222;
            break-inside: avoid; page-break-inside: avoid; }
.pointbox .pb-t { color:#1f3a5f; font-weight:bold; font-family:"Hiragino Kaku Gothic ProN",sans-serif;
                  font-size:10.5pt; margin-bottom:3px; }
"""


def build_html_str(parts, total_q):
    today = datetime.date.today().strftime("%Y年%m月")
    n_units = sum(len(p["units"]) for p in parts)
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<link rel="stylesheet" href="{B.KATEX}/katex.min.css">
<script src="{B.KATEX}/katex.min.js"></script>
<script src="{B.KATEX}/auto-render.min.js"></script>
<style>{CSS}</style></head><body>
<div class="cover"><div class="cband"></div><div class="rule"></div>
  <div class="title"><h1>{B.esc(TITLE)}</h1><div class="sub">{B.esc(SUBTITLE)}</div>
  <div class="tag">{B.esc(TAGLINE)}</div>
  <div class="meta">全{n_units}単元　計{total_q}問　·　問題編／解答・解説編</div></div>
  <div class="foot">{today}　トリリオン AI塾</div>
</div>
<div class="toc"><h2>目次</h2>{toc_html(parts)}
  <div class="howto">{B.esc(HOWTO)}</div>
</div>
<div class="divider"><h2>問題編</h2><div class="d-sub">全{n_units}単元　計{total_q}問</div></div>
{section_html(parts, 'prob')}
<div class="divider"><h2>解答・解説編</h2></div>
{section_html(parts, 'ans')}
<script>
window.onload = function(){{
  renderMathInElement(document.body, {{
    delimiters:[{{left:"$",right:"$",display:false}}], throwOnError:true, strict:false
  }});
  document.title = "done";
}};
</script></body></html>"""


def main():
    parts = C.PARTS
    # 図（あれば）を各問に差し込む。図モジュールが無い巻は何もしない。
    try:
        figs = importlib.import_module(VOL["content"].replace("content_", "figs_"))
        n_fig = figs.attach(parts)
        print(f"figures attached: {n_fig}")
    except ModuleNotFoundError:
        pass
    for p in parts:
        reorder(p["units"])
    total_q = sum(len(u["problems"]) for p in parts for u in p["units"])
    # 詳細解説の全問カバレッジ検査(欠落・余剰キーがあればビルドを止める)
    want = {f"{ui}-{q['no']}" for ui, u in
            enumerate((u for p in parts for u in p["units"]), 1) for q in u["problems"]}
    if E is not None and getattr(E, "EXPL", None):
        # EXPL(問題ごとの詳細解説)を持つ巻だけ全問カバレッジを検査する。
        # EXPL が空＝content 側の explanation を使う巻（POINTS だけのオーバーレイ）。
        missing, extra = want - set(E.EXPL), set(E.EXPL) - want
        if missing or extra:
            sys.exit(f"{VOL['expl']} 不整合: missing={sorted(missing)} extra={sorted(extra)}")
    if E is not None and getattr(E, "POINTS", None):
        n_units = sum(len(p["units"]) for p in parts)
        miss_pt = [i for i in range(1, n_units + 1) if i not in E.POINTS]
        if miss_pt:
            sys.exit(f"{VOL['expl']} の POINTS が単元 {miss_pt} に無い（単元を足したら追記する）")
    html_str = build_html_str(parts, total_q)
    html_path = os.path.join(HERE, "_build_kiso.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_str)
    subprocess.run([B.CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--virtual-time-budget=20000", f"--print-to-pdf={OUT}",
                    "file://" + html_path], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    B.stamp_pdf(OUT, BOOK)
    d = fitz.open(OUT)
    print(f"WROTE {OUT} | pages: {d.page_count} | units: {sum(len(p['units']) for p in parts)} | questions: {total_q}")
    d.close()


if __name__ == "__main__":
    main()
