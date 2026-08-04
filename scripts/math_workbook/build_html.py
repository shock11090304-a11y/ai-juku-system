#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数学 問題演習テキスト(数IA/数IIB)を KaTeX 教科書組版で PDF 化する。

  python3 build_html.py ia
  python3 build_html.py iib

content_ia/content_iib の stem/answer/explanation/choices に埋め込んだ $...$ を
KaTeX(自己ホスト vendor/katex, オーバーアロー/組分数/√被覆すべて教科書準拠)で描画。
HTML → Chrome --headless --print-to-pdf → fitz で通しノンブル(ページ番号)+柱を刻印。
"""
import sys, os, subprocess, importlib, datetime, html
import fitz

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
KATEX = "file://" + os.path.join(REPO, "vendor", "katex")
FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
if not os.path.exists(FONT_PATH):
    FONT_PATH = "/Library/Fonts/Arial Unicode.ttf"

NAVY = (0x1f/255, 0x3a/255, 0x5f/255)
GRAY = (0x8a/255, 0x8a/255, 0x8a/255)

LEVEL = {"basic": ("基礎", "#3a7d44"), "standard": ("標準", "#b06a1f"), "advanced": ("発展", "#a03030")}
CIRCLED = ["①", "②", "③", "④", "⑤"]

def esc(s):
    # &<> をエスケープ($..$ 内の LaTeX は \leqq 等を使い生の <> を含めない前提)
    return html.escape("" if s is None else str(s), quote=False)

def prob_html(q):
    lvl = LEVEL.get(q.get("level"))
    tag = f'<span class="lv" style="color:{lvl[1]}">[{lvl[0]}]</span> ' if lvl else ""
    out = [f'<div class="prob"><span class="no">{q["no"]}.</span> {tag}<span class="stem">{esc(q["stem"])}</span>']
    if q.get("type") == "mc":
        chs = "　".join(f'{CIRCLED[i]} {esc(c)}' for i, c in enumerate(q.get("choices", [])))
        out.append(f'<div class="choices">{chs}</div>')
    if q.get("figure"):  # 図(SVG)はそのまま埋め込む(エスケープしない)
        out.append(f'<div class="fig">{q["figure"]}</div>')
    out.append("</div>")
    return "".join(out)

def ans_html(q):
    if q.get("type") == "mc":
        a = f'{CIRCLED[q.get("answer_index",0)]}　{esc(q.get("answer",""))}'
    else:
        a = esc(q.get("answer", ""))
    return (f'<div class="prob"><span class="no">{q["no"]}.</span> '
            f'<span class="ans">{a}</span>'
            f'<div class="exp">{esc(q.get("explanation",""))}</div></div>')

def units_section(units, kind):
    """kind: 'prob' or 'ans'"""
    parts = []
    for i, u in enumerate(units, 1):
        parts.append('<section class="unit">')
        kicker = "問題" if kind == "prob" else "解答"
        parts.append(f'<div class="band"><div class="band-k">{kicker}　{i:02d}</div>'
                     f'<div class="band-t">{esc(u["name"])}</div></div>')
        cur = None
        render = prob_html if kind == "prob" else ans_html
        for q in u["problems"]:
            g = q.get("group", "")
            if g != cur:
                cur = g
                parts.append(f'<h3 class="grp">■ {esc(g)}</h3>')
            parts.append(render(q))
        parts.append('</section>')
    return "\n".join(parts)

def build_html(cfg, units, total_q):
    today = datetime.date.today().strftime("%Y年%m月")
    toc = []
    for i, u in enumerate(units, 1):
        toc.append(f'<div class="toc-row"><span class="toc-no">{i:02d}</span>'
                   f'<span class="toc-name">{esc(u["name"])}</span>'
                   f'<span class="toc-tag">{esc(u.get("tag",""))}</span>'
                   f'<span class="toc-n">{len(u["problems"])}問</span></div>')
    css = """
    @page { size: A4; margin: 20mm 18mm 17mm 18mm; }
    * { box-sizing: border-box; }
    body { font-family: "Hiragino Mincho ProN","Yu Mincho",serif; color:#1a1a1a; font-size:10.5pt; line-height:1.65; margin:0; }
    .sans { font-family:"Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif; }
    .katex { font-size:1.02em; }
    /* 表紙 */
    .cover { height: 247mm; position: relative; page-break-after: always; }
    .cover .band { position:absolute; top:-20mm; left:-18mm; width:210mm; height:70mm; background:#1f3a5f; }
    .cover .rule { position:absolute; top:50mm; left:-18mm; width:210mm; height:2mm; background:#c8a24e; }
    .cover .title { position:absolute; top:92mm; width:100%; text-align:center; font-family:"Hiragino Kaku Gothic ProN",sans-serif; }
    .cover .title h1 { color:#1f3a5f; font-size:30pt; margin:0; letter-spacing:2px; }
    .cover .title .sub { color:#1f3a5f; font-size:15pt; margin-top:6px; }
    .cover .title .tag { color:#444; font-size:12.5pt; margin-top:18px; font-weight:normal; }
    .cover .title .meta { color:#444; font-size:11.5pt; margin-top:6px; }
    .cover .foot { position:absolute; top:180mm; width:100%; text-align:center; color:#8a8a8a; font-size:10.5pt; font-family:sans-serif; }
    /* 部扉 */
    .divider { height:247mm; page-break-before:always; page-break-after:always; display:flex; flex-direction:column; justify-content:center; align-items:center; }
    .divider h2 { color:#1f3a5f; font-size:22pt; font-family:"Hiragino Kaku Gothic ProN",sans-serif; margin:0; }
    .divider .d-sub { color:#444; font-size:12pt; margin-top:8px; }
    /* 目次 */
    .toc { page-break-after: always; }
    .toc h2 { color:#1f3a5f; text-align:center; font-size:20pt; font-family:"Hiragino Kaku Gothic ProN",sans-serif; }
    .toc-row { display:flex; align-items:center; border-bottom:0.5px solid #c9d4e0; padding:6px 2px; }
    .toc-no { color:#1f3a5f; font-weight:bold; width:34px; font-family:sans-serif; }
    .toc-name { flex:0 0 40%; font-family:"Hiragino Kaku Gothic ProN",sans-serif; }
    .toc-tag { flex:1; color:#8a8a8a; font-size:9.5pt; }
    .toc-n { color:#8a8a8a; font-size:9.5pt; }
    .howto { margin-top:14px; color:#444; font-size:10pt; background:#f4f6f9; border-left:3px solid #c8a24e; padding:10px 12px; }
    /* 分野 */
    .unit { page-break-before: always; }
    .band { background:#1f3a5f; color:#fff; padding:8px 12px 10px; margin-bottom:8px; }
    .band-k { font-size:10pt; font-family:sans-serif; opacity:.9; }
    .band-t { font-size:16pt; font-family:"Hiragino Kaku Gothic ProN",sans-serif; margin-top:1px; }
    .grp { color:#1f3a5f; font-size:11pt; font-family:"Hiragino Kaku Gothic ProN",sans-serif; margin:10px 0 4px; break-after: avoid; page-break-after: avoid; }
    .prob { margin:3px 0 4px; padding-left:17px; text-indent:-17px; break-inside: avoid; page-break-inside: avoid; }
    .prob .no { color:#1f3a5f; font-weight:bold; }
    .lv { font-size:8pt; }
    .choices { text-indent:0; padding-left:20px; margin-top:1px; }
    .ans { color:#c8492e; font-weight:bold; }
    .exp { text-indent:0; padding-left:2px; color:#333; font-size:9.5pt; margin-top:1px; }
    .fig { text-indent:0; text-align:center; margin:5px 0 3px; }
    .fig svg { max-width:66mm; max-height:46mm; height:auto; }
    .fig svg text { font-family:"Hiragino Kaku Gothic ProN",sans-serif; }
    """
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<link rel="stylesheet" href="{KATEX}/katex.min.css">
<script src="{KATEX}/katex.min.js"></script>
<script src="{KATEX}/auto-render.min.js"></script>
<style>{css}</style></head><body>
<div class="cover"><div class="band"></div><div class="rule"></div>
  <div class="title"><h1>{esc(cfg['title'])}</h1><div class="sub">{esc(cfg['subtitle'])}</div>
  <div class="tag">{esc(cfg['tagline'])}</div>
  <div class="meta">全{len(units)}分野　計{total_q}問　·　問題編／解答・解説編</div></div>
  <div class="foot">{today}　トリリオン AI塾</div>
</div>
<div class="toc"><h2>目次</h2>{''.join(toc)}
  <div class="howto">{cfg['howto']}</div>
</div>
<div class="divider"><h2>問題編</h2><div class="d-sub">全{len(units)}分野　計{total_q}問</div></div>
{units_section(units, 'prob')}
<div class="divider"><h2>解答・解説編</h2></div>
{units_section(units, 'ans')}
<script>
window.onload = function(){{
  renderMathInElement(document.body, {{
    delimiters:[{{left:"$",right:"$",display:false}}], throwOnError:true, strict:false
  }});
  document.title = "done";
}};
</script></body></html>"""

def stamp_pdf(path, book_title):
    """通しノンブル(中央下)＋柱(左上に書名)を全ページに刻印。表紙(1p目)は除く。"""
    doc = fitz.open(path)
    fnt = fitz.Font(fontfile=FONT_PATH)
    for i, page in enumerate(doc):
        if i == 0:
            continue  # 表紙
        w, h = page.rect.width, page.rect.height
        page.insert_text((51, 34), book_title, fontfile=FONT_PATH, fontname="AU",
                         fontsize=8, color=GRAY)
        n = str(i)  # 表紙を0とみなし2ページ目=1
        tw = fnt.text_length(n, fontsize=9)
        page.insert_text((w/2 - tw/2, h - 22), n, fontfile=FONT_PATH, fontname="AU",
                         fontsize=9, color=GRAY)
    doc.subset_fonts()  # 埋め込みフォントを使用グリフのみに(Arial Unicode 23MB→数KB)
    tmp = path + ".tmp"
    doc.save(tmp, garbage=4, deflate=True, clean=True)
    doc.close()
    os.replace(tmp, path)

CONFIGS = {
    "ia": dict(module="content_ia", title="数学 I · A", subtitle="問題演習テキスト",
        tagline="高校2年 / 苦手克服・基礎〜標準の総点検", out="数学IA_問題演習テキスト.pdf",
        book="数学 I·A 問題演習テキスト",
        howto=("【使い方】この問題集は「問題編」と「解答・解説編」に分かれています。各分野を解いたら、"
               "必ず解答・解説編で答え合わせをしてください。まず全問を自力で解き、間違えた問題に印をつけて"
               "解き直すと、苦手が確実に埋まります。")),
    "iib": dict(module="content_iib", title="数学 II · B", subtitle="問題演習テキスト",
        tagline="高校2年 / 苦手克服・基礎〜標準の総点検", out="数学IIB_問題演習テキスト.pdf",
        book="数学 II·B 問題演習テキスト",
        howto=("【使い方】この問題集は「問題編」と「解答・解説編」に分かれています。各分野を解いたら、"
               "必ず解答・解説編で答え合わせをしてください。まず全問を自力で解き、間違えた問題を解き直すと"
               "苦手が埋まります。数式・記号は教科書と同じ表記で組んでいます。")),
    "ia2": dict(module="content_ia_v2", title="数学 I · A", subtitle="問題演習テキスト 第2集（図形強化）",
        tagline="高校2年 / 図形問題を図つきで増強・前集と重複なし", out="数学IA_問題演習テキスト_第2集_図形強化.pdf",
        book="数学 I·A 問題演習テキスト 第2集",
        howto=("【使い方】この問題集は前集(第1集)と重複しない新しい問題で構成し、図形分野を図つきで手厚くしました。"
               "「問題編」と「解答・解説編」に分かれています。図をよく見て、まず自力で解き、"
               "解答・解説編で答え合わせをしてください。数式・記号は教科書と同じ表記です。")),
    "iib2": dict(module="content_iib_v2", title="数学 II · B", subtitle="問題演習テキスト 第2集（図形強化）",
        tagline="高校2年 / 図形問題を図つきで増強・前集と重複なし", out="数学IIB_問題演習テキスト_第2集_図形強化.pdf",
        book="数学 II·B 問題演習テキスト 第2集",
        howto=("【使い方】この問題集は前集(第1集)と重複しない新しい問題で構成し、図形と方程式・ベクトル等を"
               "図つきで手厚くしました。「問題編」と「解答・解説編」に分かれています。図をよく見て、まず自力で解き、"
               "解答・解説編で答え合わせをしてください。数式・記号は教科書と同じ表記です。")),
}

def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "ia"
    cfg = CONFIGS[which]
    mod = importlib.import_module(cfg["module"])
    units = mod.UNITS
    # 同じ group の問題を(初出順を保って)連続させる。追加問題が末尾に付いても
    # 見出しが重複せず、レイアウトが分断されないようにする。
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
    total_q = sum(len(u["problems"]) for u in units)
    html_str = build_html(cfg, units, total_q)
    html_path = os.path.join(HERE, f"_build_{which}.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_str)
    out_path = os.path.join(HERE, cfg["out"])
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--virtual-time-budget=20000", f"--print-to-pdf={out_path}",
                    "file://" + html_path], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    stamp_pdf(out_path, cfg["book"])
    d = fitz.open(out_path)
    print(f"WROTE {out_path} | pages: {d.page_count} | units: {len(units)} | questions: {total_q}")
    d.close()

if __name__ == "__main__":
    main()
