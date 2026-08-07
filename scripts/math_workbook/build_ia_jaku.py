#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数学I·A 弱点発見トレーニング を KaTeX 教科書組版で PDF 化する。

  python3 build_ia_jaku.py

content_ia_jaku.PARTS(8編18単元)を編の扉+攻略ボックスつきで問題編/解答編に組む。
描画部品(stamp_pdf / esc / KATEX / CHROME)は build_html から、CSS は build_kiso から再利用。

★単元番号は A01〜A18(接頭辞 A 必須)。第1集=01〜12 / 第2集=13〜27 / 化学=C01〜C18 と
  番号が衝突すると、採点シートの写真から番号を回収したときにどの教材の×か判別できない。
"""
import os, re, sys, subprocess, datetime
import fitz
import build_html as B
import build_kiso as K          # CSS と reorder を再利用
import content_ia_jaku as C
import _ia_jaku_lib as L

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "数学IA_弱点発見トレーニング.pdf")

# 表紙に出す宛名。★コードに書かない（PUBLIC リポジトリなので公開される）。
#   刷るときだけ:  STUDENT_NAME="姓 名" python3 build_ia_jaku.py    空なら汎用版。
STUDENT = os.environ.get("STUDENT_NAME", "")
TITLE = "弱点発見トレーニング"
SUBTITLE = "数学 I · A 全範囲［診断つき問題集］"
TAGLINE = "解いて採点するだけで、どの単元のどこが崩れているかが分かる"
BOOK = "数学 I·A 弱点発見トレーニング"
HOWTO = ("【この問題集の使い方】数学I·A の全範囲を、単元ごとに「基礎 → 標準 → 発展」の順に並べました。"
         "この本のねらいは、点を取ることより先に、<b>どこでつまずいているかを見つける</b>ことです。"
         "だから、分からない問題は飛ばさずに、<b>飛ばしたことが分かるように空欄のまま</b>にしてください。"
         "各編のとびらにある「攻略の手順」を先に読んでから解き始めること。"
         "解き終わったら付属の<b>自己採点シート</b>に ○ ×（公式を見て解けたときは △）を記録し、"
         "その写真を先生に送ってください。"
         "解説は途中の式を省いていません。分からなかった問題は、解説をノートに写してから、"
         "何も見ずにもう一度解くのが最強の勉強法です。")


def toc_html(parts):
    rows = []
    codes = iter(C.CODES)
    for p in parts:
        rows.append(f'<div class="toc-part">{B.esc(p["area"])}</div>')
        for u in p["units"]:
            rows.append(
                f'<div class="toc-row"><span class="toc-no">{next(codes)}</span>'
                f'<span class="toc-name">{B.esc(u["name"])}</span>'
                f'<span class="toc-tag">{B.esc(u.get("tag",""))}</span>'
                f'<span class="toc-n">{len(u["problems"])}問</span></div>')
    return "".join(rows)


ALLOW_TAGS = (("&lt;b&gt;", "<b>"), ("&lt;/b&gt;", "</b>"), ("&lt;br&gt;", "<br>"))


def unesc(s):
    """esc 済み文字列のうち、教材で使ってよいタグ(<b>/<br>)だけ復元する。"""
    for a, b in ALLOW_TAGS:
        s = s.replace(a, b)
    return s


def detail(s):
    """解説テキスト → HTML。<b>/<br> は生かし、実改行を <br> に。"""
    return unesc(B.esc(s)).replace("\n", "<br>")


def prob_html(q):
    """問題行。stem の <b>/<br> を通し、figure(SVG)はエスケープせず埋め込む。"""
    lvl = B.LEVEL.get(q.get("level"))
    tag = f'<span class="lv" style="color:{lvl[1]}">[{lvl[0]}]</span> ' if lvl else ""
    out = [f'<div class="prob"><span class="no">{q["no"]}.</span> {tag}'
           f'<span class="stem">{unesc(B.esc(q["stem"]))}</span>']
    if q.get("figure"):
        out.append(f'<div class="fig">{q["figure"]}</div>')
    out.append("</div>")
    return "".join(out)


def ans_html(q):
    return (f'<div class="prob"><div class="ansline"><span class="no">{q["no"]}.</span> '
            f'<span class="ans">{B.esc(q.get("answer",""))}</span></div>'
            f'<div class="exp">{detail(q.get("explanation",""))}</div></div>')


def section_html(parts, kind):
    out = []
    codes = iter(C.CODES)
    kicker = "問題" if kind == "prob" else "解答"
    for p in parts:
        # ★攻略ボックスは問題編だけに出す。両方に出すと同じ8ページが丸ごと重複する。
        pts = C.PART_POINTS.get(p["area"], "") if kind == "prob" else ""
        box = (f'<div class="pointbox pdivbox"><div class="pb-t">◆ 攻略の手順（先に読む）</div>{detail(pts)}'
               f'<div class="pb-n">※ この手順を見ながら解いた問題は、自己採点シートで '
               f'<b>△</b>（見て解けた）にしてください。○ と △ を分けて記録することが、'
               f'そのまま診断の精度になります。</div></div>' if pts else "")
        out.append(f'<div class="pdiv"><h2>{B.esc(p["area"])}</h2>'
                   f'<div class="d-sub">{B.esc(p.get("sub",""))}</div>{box}</div>')
        for u in p["units"]:
            code = next(codes)
            out.append('<section class="unit">')
            out.append(f'<div class="band"><div class="band-k">{kicker}　{code}</div>'
                       f'<div class="band-t">{B.esc(u["name"])}</div></div>')
            cur = None
            for q in u["problems"]:
                g = q.get("group", "")
                if g != cur:
                    cur = g
                    out.append(f'<h3 class="grp">■ {B.esc(g)}</h3>')
                out.append(prob_html(q) if kind == "prob" else ans_html(q))
            out.append('</section>')
    return "\n".join(out)


EXTRA_CSS = """
/* 編の扉に攻略ボックスを置くのでレイアウトを調整 */
.pdiv { page-break-before:always; padding-top:30mm; text-align:center; }
.pdivbox { text-align:left; margin:14mm auto 0; max-width:152mm; }
.cover .who { position:absolute; top:150mm; width:100%; text-align:center;
  font-family:"Hiragino Kaku Gothic ProN",sans-serif; color:#1f3a5f; font-size:13pt; }
.cover .who span { border-bottom:1.4px solid #c8a24e; padding:0 26px 4px; }

/* ★組分数(\\dfrac)の高さを行送りが吸収できず、上の行の分母と下の行の分子が
   物理的に重なる(数字の誤読が起きるレベル)。解説・攻略ボックスとも行送りを広げる。
   解説内は \\frac に統一済み(unit_check_ia_jaku.py が \\dfrac を弾く)。 */
.exp { line-height: 2.1; }
.pointbox { line-height: 2.45; }        /* 攻略ボックスは \\frac だが行が長いので広く取る */
.exp .katex, .pointbox .katex { line-height: 1.2; }   /* 数式内部は詰めたまま */
/* ★インラインの \frac は分子分母が 0.7em に落ち、指数の中に入るとさらに 0.49em になる。
   本文 10.5pt では 4.4pt(=1.5mm)まで縮んで紙で読めなかった(実測3336グリフが 6.6pt 未満)。
   解説の数式だけ一回り大きくして底上げする。ia_jaku_gate.py が最小グリフサイズを見張る。 */
.exp .katex { font-size: 1.16em; }
.pointbox .katex { font-size: 1.10em; }
.prob .stem { line-height: 1.9; }
/* ★答え行も行送りを上げる。場合分けの答えは1行に収まらず折り返すことがあり、
   既定(1.65)のままだと上の行の $\\leqq$ に下の行の数字が乗る(p54/p63 で実測)。 */
.prob .ansline { line-height: 1.95; }
.prob .ansline .katex { line-height: 1.2; }
/* 1問=1ブロックで改ページ位置を決める(解説末尾だけが次ページに落ちる孤立行を防ぐ)。
   build_kiso.CSS の `.prob:has(.exp br){break-inside:auto}` は詳細度が高いので同詳細度で上書き。 */
.prob, .prob:has(.exp br) { break-inside: avoid; page-break-inside: avoid; }
.exp, .pointbox { orphans: 3; widows: 3; }
.ansline { break-after: avoid; page-break-after: avoid; }
/* 図 */
.fig { margin:6px 0 2px 26px; }
.fig svg { max-width:100%; height:auto; }
/* 目次の番号列は A01 の3文字が入る幅にする */
.toc-no { min-width: 34px; }
.pb-n { margin-top:10px; padding-top:8px; border-top:0.6px solid #c8a24e; font-size:9.5pt;
        color:#555; line-height:1.7; }
"""


def build_html_str(parts, total_q):
    today = datetime.date.today().strftime("%Y年%m月")
    n_units = sum(len(p["units"]) for p in parts)
    who = (f'<div class="who"><span>{B.esc(STUDENT)} さん 専用</span></div>' if STUDENT else "")
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<link rel="stylesheet" href="{B.KATEX}/katex.min.css">
<script src="{B.KATEX}/katex.min.js"></script>
<script src="{B.KATEX}/auto-render.min.js"></script>
<style>{K.CSS}{EXTRA_CSS}</style></head><body>
<div class="cover"><div class="cband"></div><div class="rule"></div>
  <div class="title"><h1>{B.esc(TITLE)}</h1><div class="sub">{B.esc(SUBTITLE)}</div>
  <div class="tag">{B.esc(TAGLINE)}</div>
  <div class="meta">全{n_units}単元　計{total_q}問　·　問題編／解答・解説編</div></div>
  {who}
  <div class="foot">{today}　トリリオン AI塾</div>
</div>
<div class="toc"><h2>目次</h2>{toc_html(parts)}
  <div class="howto">{detail(HOWTO)}</div>
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


BAND_RE = re.compile(r"(問題|解答)\s*(A\d\d)")


def stamp_units(path):
    """柱の右側に「A07 2次関数の最大・最小」を刻印する。

    ★これが無いと、解答編の2ページ目以降は「■置き換えて因数分解」から始まり、
      どの単元の解答かページ上から分からない(柱は書名だけ)。18単元100ページ超では
      採点シートの番号と付き合わせるのに毎回めくり戻す必要がある。
    """
    name_of = dict(zip(C.CODES, (u["name"] for u in C.UNITS)))
    doc = fitz.open(path)
    fnt = fitz.Font(fontfile=B.FONT_PATH)
    cur = None
    for i, page in enumerate(doc):
        if i == 0:
            continue
        txt = page.get_text()
        m = BAND_RE.search(txt)
        if m:
            cur = m.group(2)
        elif ("問題編" in txt or "解答・解説編" in txt
              or any(a["area"] in txt for a in C.PARTS)):
            cur = None                      # 大扉・編の部扉では前の単元名を引きずらない
        if not cur:
            continue
        label = f"{cur}　{name_of.get(cur, '')}"
        w = page.rect.width
        tw = fnt.text_length(label, fontsize=8)
        page.insert_text((w - 51 - tw, 34), label, fontfile=B.FONT_PATH, fontname="AU",
                         fontsize=8, color=B.GRAY)
    tmp = path + ".tmp"       # subset はしない(このあと stamp_pdf が刻印してからまとめて削る)
    doc.save(tmp, garbage=4, deflate=True, clean=True)
    doc.close()
    os.replace(tmp, path)


def main():
    parts = C.PARTS
    for p in parts:
        K.reorder(p["units"])
    total_q = sum(len(u["problems"]) for p in parts for u in p["units"])
    missing = [f'{code}-{q["no"]}' for code, u in zip(C.CODES, C.UNITS)
               for q in u["problems"] if not q.get("explanation", "").strip()]
    if missing:
        sys.exit(f"解説が空の問題: {missing}")
    html_path = os.path.join(HERE, "_build_ia_jaku.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(build_html_str(parts, total_q))
    subprocess.run([B.CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--virtual-time-budget=30000", f"--print-to-pdf={OUT}",
                    "file://" + html_path], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    stamp_units(OUT)      # ★必ず stamp_pdf より先。後に回すと subset_fonts 後で字が無く NUL になる
    B.stamp_pdf(OUT, BOOK)
    d = fitz.open(OUT)
    print(f"WROTE {OUT} | pages: {d.page_count} | units: {len(C.UNITS)} | questions: {total_q}")
    d.close()


if __name__ == "__main__":
    main()
